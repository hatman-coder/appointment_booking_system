import calendar
import json
import logging
from datetime import date, datetime

from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.account.models import User

from .selectors import ReportSelector
from .services import ReportServices

logger = logging.getLogger(__name__)


def standardize_response(success: bool, message: str, data=None, status_code=None):
    """
    Standardize API response format
    """
    response_data = {"success": success, "message": message}

    if data is not None:
        if isinstance(data, dict):
            response_data.update(data)
        else:
            response_data["data"] = data

    if status_code is None:
        status_code = status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST

    return Response(response_data, status=status_code)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def generate_monthly_report(request, doctor_id=None):
    """
    Generate or retrieve monthly report for a doctor
    GET/POST /api/reports/monthly/{doctor_id}/
    OR
    GET/POST /api/reports/monthly/ (for doctor's own report)
    """
    try:
        # Determine target doctor
        if doctor_id:
            target_doctor_id = doctor_id
            # Check permissions
            if (
                request.user.user_type == UserType.DOCTOR.value
                and request.user.id != doctor_id
            ):
                return standardize_response(
                    False,
                    "Cannot access other doctors' reports",
                    status_code=status.HTTP_403_FORBIDDEN,
                )
            elif request.user.user_type == UserType.PATIENT.value:
                return standardize_response(
                    False,
                    "Patients cannot access doctor reports",
                    status_code=status.HTTP_403_FORBIDDEN,
                )
        else:
            # Own report (doctor only)
            if request.user.user_type != UserType.DOCTOR.value:
                return standardize_response(
                    False,
                    "Only doctors can access their own reports without specifying doctor ID",
                    status_code=status.HTTP_403_FORBIDDEN,
                )
            target_doctor_id = request.user.id

        # Get parameters
        if request.method == "GET":
            year = int(request.GET.get("year", timezone.now().year))
            month = int(request.GET.get("month", timezone.now().month))
            force_regenerate = (
                request.GET.get("force_regenerate", "false").lower() == "true"
            )
        else:  # POST
            year = request.data.get("year", timezone.now().year)
            month = request.data.get("month", timezone.now().month)
            force_regenerate = request.data.get("force_regenerate", False)

        # Validate parameters
        if not (1 <= month <= 12):
            return standardize_response(
                False,
                "Month must be between 1 and 12",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Generate report
        result = ReportServices.generate_monthly_doctor_report(
            target_doctor_id, year, month, force_regenerate
        )

        if result["success"]:
            return standardize_response(
                True,
                result["message"],
                {
                    "report": result["report"],
                    "generated_at": result["generated_at"],
                    "from_cache": result["from_cache"],
                },
                status_code=status.HTTP_200_OK,
            )
        else:
            return standardize_response(
                False, result["message"], status_code=status.HTTP_400_BAD_REQUEST
            )

    except ValueError:
        return standardize_response(
            False,
            "Invalid year or month parameter",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.error(f"Generate monthly report API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to generate monthly report",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_system_monthly_report(request):
    """
    Get system-wide monthly report (Admin only)
    GET /api/reports/system/monthly/
    """
    try:
        # Check admin permission
        if request.user.user_type != UserType.ADMIN.value:
            return standardize_response(
                False,
                "Admin privileges required",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # Get parameters
        year = int(request.GET.get("year", timezone.now().year))
        month = int(request.GET.get("month", timezone.now().month))

        # Generate system report
        result = ReportServices.generate_system_monthly_report(year, month)

        if result["success"]:
            return standardize_response(
                True,
                result["message"],
                {"system_report": result["report"]},
                status_code=status.HTTP_200_OK,
            )
        else:
            return standardize_response(
                False,
                result["message"],
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except ValueError:
        return standardize_response(
            False, "Invalid parameters", status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Get system monthly report API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to generate system monthly report",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_doctor_annual_summary(request, doctor_id=None):
    """
    Get doctor's annual summary report
    GET /api/reports/annual/{doctor_id}/
    """
    try:
        # Determine target doctor
        if doctor_id:
            target_doctor_id = doctor_id
            # Check permissions
            if (
                request.user.user_type == UserType.DOCTOR.value
                and request.user.id != doctor_id
            ):
                return standardize_response(
                    False,
                    "Cannot access other doctors' annual summaries",
                    status_code=status.HTTP_403_FORBIDDEN,
                )
        else:
            if request.user.user_type != UserType.DOCTOR.value:
                return standardize_response(
                    False,
                    "Only doctors can access their own annual summary",
                    status_code=status.HTTP_403_FORBIDDEN,
                )
            target_doctor_id = request.user.id

        # Get parameters
        year = int(request.GET.get("year", timezone.now().year))

        # Generate annual summary
        result = ReportServices.generate_doctor_annual_summary(target_doctor_id, year)

        if result["success"]:
            return standardize_response(
                True,
                result["message"],
                {"annual_summary": result},
                status_code=status.HTTP_200_OK,
            )
        else:
            return standardize_response(
                False, result["message"], status_code=status.HTTP_400_BAD_REQUEST
            )

    except ValueError:
        return standardize_response(
            False, "Invalid year parameter", status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Get annual summary API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to generate annual summary",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_dashboard_analytics(request):
    """
    Get analytics data for dashboard based on user type
    GET /api/reports/dashboard/
    """
    try:
        current_year = timezone.now().year
        current_month = timezone.now().month

        if request.user.user_type == UserType.PATIENT.value:
            # Patient dashboard analytics
            patient_stats = ReportSelector.get_patient_report_summary(request.user.id)

            return standardize_response(
                True,
                "Patient dashboard analytics retrieved",
                {"patient_analytics": patient_stats},
                status_code=status.HTTP_200_OK,
            )

        elif request.user.user_type == UserType.DOCTOR.value:
            # Doctor dashboard analytics
            current_report = ReportServices.generate_monthly_doctor_report(
                request.user.id, current_year, current_month
            )

            recent_reports = ReportSelector.get_doctor_recent_reports(
                request.user.id, 6
            )

            trends = []
            for report in recent_reports:
                trends.append(
                    {
                        "month": report.report_month,
                        "year": report.report_year,
                        "month_name": calendar.month_name[report.report_month],
                        "appointments": report.total_appointments,
                        "earnings": float(report.total_earnings),
                        "patients": report.total_patients,
                    }
                )

            return standardize_response(
                True,
                "Doctor dashboard analytics retrieved",
                {
                    "current_month_report": (
                        current_report["report"] if current_report["success"] else None
                    ),
                    "trends": trends,
                    "recent_reports_count": len(recent_reports),
                },
                status_code=status.HTTP_200_OK,
            )

        elif request.user.user_type == UserType.ADMIN.value:
            # Admin dashboard analytics
            system_report = ReportServices.generate_system_monthly_report(
                current_year, current_month
            )
            report_stats = ReportServices.get_report_statistics()

            return standardize_response(
                True,
                "Admin dashboard analytics retrieved",
                {
                    "system_report": (
                        system_report["report"] if system_report["success"] else None
                    ),
                    "report_statistics": report_stats.get("statistics", {}),
                    "generated_at": timezone.now(),
                },
                status_code=status.HTTP_200_OK,
            )

        else:
            return standardize_response(
                False, "Invalid user type", status_code=status.HTTP_403_FORBIDDEN
            )

    except Exception as e:
        logger.error(f"Get dashboard analytics API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to retrieve dashboard analytics",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def bulk_generate_reports(request):
    """
    Bulk generate monthly reports (Admin only)
    POST /api/reports/admin/bulk-generate/
    """
    try:
        if request.user.user_type != UserType.ADMIN.value:
            return standardize_response(
                False,
                "Admin privileges required",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        year = request.data.get("year", timezone.now().year)
        month = request.data.get("month", timezone.now().month)
        doctor_ids = request.data.get("doctor_ids")

        result = ReportServices.bulk_generate_monthly_reports(year, month, doctor_ids)

        if result["success"]:
            return standardize_response(
                True,
                result["message"],
                result["results"],
                status_code=status.HTTP_200_OK,
            )
        else:
            return standardize_response(
                False,
                result["message"],
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        logger.error(f"Bulk generate reports API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to perform bulk report generation",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_report_statistics(request):
    """
    Get report statistics for admin dashboard (Admin only)
    GET /api/reports/admin/statistics/
    """
    try:
        if request.user.user_type != UserType.ADMIN.value:
            return standardize_response(
                False,
                "Admin privileges required",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        result = ReportServices.get_report_statistics()

        if result["success"]:
            return standardize_response(
                True,
                "Report statistics retrieved successfully",
                result["statistics"],
                status_code=status.HTTP_200_OK,
            )
        else:
            return standardize_response(
                False,
                result["message"],
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        logger.error(f"Get report statistics API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to retrieve report statistics",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def health_check(request):
    """
    Health check endpoint for report service
    GET /api/reports/health/
    """
    try:
        report_count = ReportSelector.get_all_monthly_reports().count()
        latest_report = ReportSelector.get_all_monthly_reports().first()

        health_data = {
            "status": "healthy",
            "timestamp": timezone.now(),
            "total_reports": report_count,
            "latest_report_date": latest_report.generated_at if latest_report else None,
            "service_version": "1.0.0",
        }

        return standardize_response(
            True,
            "Report service is healthy",
            health_data,
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return standardize_response(
            False,
            "Report service health check failed",
            {"error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

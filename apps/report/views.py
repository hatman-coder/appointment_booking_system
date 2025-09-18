from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.core.paginator import Paginator
from .selectors import ReportSelector
from .services import ReportService
import logging

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def monthly_reports_list(request):
    """List monthly reports with filtering and pagination"""
    user = request.user

    # Get queryset based on user type
    if user.user_type == "admin":
        reports = ReportSelector.get_all_monthly_reports()
    elif user.user_type == "doctor":
        reports = ReportSelector.get_doctor_monthly_reports(user.doctor_profile.id)
    else:
        return Response(
            {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
        )

    # Apply filters
    month = request.GET.get("month")
    year = request.GET.get("year")
    doctor_id = request.GET.get("doctor")

    if month:
        reports = reports.filter(month=month)
    if year:
        reports = reports.filter(year=year)
    if doctor_id and user.user_type == "admin":
        reports = reports.filter(doctor_id=doctor_id)

    # Pagination
    page = request.GET.get("page", 1)
    paginator = Paginator(reports, 20)
    page_obj = paginator.get_page(page)

    # Manual data formatting
    reports_data = []
    for report in page_obj:
        reports_data.append(
            {
                "id": report.id,
                "doctor_id": report.doctor.id,
                "doctor_name": report.doctor.user.full_name,
                "month": report.month,
                "year": report.year,
                "total_patients": report.total_patients,
                "total_appointments": report.total_appointments,
                "total_earnings": float(report.total_earnings),
                "created_at": report.created_at.isoformat(),
                "updated_at": report.updated_at.isoformat(),
            }
        )

    return Response(
        {
            "reports": reports_data,
            "pagination": {
                "current_page": page_obj.number,
                "total_pages": paginator.num_pages,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
                "total_count": paginator.count,
            },
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def generate_monthly_report(request):
    """Generate monthly report for a doctor"""
    if request.user.user_type not in ["admin", "doctor"]:
        return Response(
            {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
        )

    doctor_id = request.data.get("doctor_id")
    month = request.data.get("month")
    year = request.data.get("year")

    if not all([doctor_id, month, year]):
        return Response(
            {"error": "doctor_id, month, and year are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if user can generate report for this doctor
    if request.user.user_type == "doctor" and request.user.doctor_profile.id != int(
        doctor_id
    ):
        return Response(
            {"error": "Can only generate reports for yourself"},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        report = ReportService.generate_monthly_report(
            int(doctor_id), int(month), int(year)
        )

        # Manual data formatting
        report_data = {
            "id": report.id,
            "doctor_id": report.doctor.id,
            "doctor_name": report.doctor.user.full_name,
            "month": report.month,
            "year": report.year,
            "total_patients": report.total_patients,
            "total_appointments": report.total_appointments,
            "total_earnings": float(report.total_earnings),
            "created_at": report.created_at.isoformat(),
            "updated_at": report.updated_at.isoformat(),
        }

        return Response(
            {"message": "Monthly report generated successfully", "report": report_data},
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        return Response(
            {"error": "Failed to generate report"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

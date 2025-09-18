from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List, Tuple
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django.core.cache import cache
from decimal import Decimal
import calendar
import logging

from .models import MonthlyReport
from .selectors import ReportSelector
from apps.appointment.models import Appointment
from apps.account.models import User

logger = logging.getLogger(__name__)


class ReportGenerationError(Exception):
    """Custom exception for report generation errors"""

    pass


class ReportServices:
    """Service class for report-related business operations"""

    # Cache configuration
    CACHE_TIMEOUT = 3600 * 6  # 6 hours (reports change less frequently)
    CACHE_PREFIX = "report_"

    @staticmethod
    def get_month_date_range(year: int, month: int) -> Tuple[date, date]:
        """
        Get the first and last day of a given month
        """
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        return first_day, last_day

    @staticmethod
    def calculate_doctor_monthly_stats(
        doctor_id: int, year: int, month: int
    ) -> Dict[str, Any]:
        """
        Calculate monthly statistics for a specific doctor
        """
        try:
            first_day, last_day = ReportServices.get_month_date_range(year, month)

            # Get doctor
            try:
                doctor = User.objects.get(id=doctor_id, user_type=UserType.DOCTOR.value)
            except User.DoesNotExist:
                raise ReportGenerationError(f"Doctor with ID {doctor_id} not found")

            # Get appointments for the month
            appointments = Appointment.objects.filter(
                doctor_id=doctor_id,
                appointment_date__gte=first_day,
                appointment_date__lte=last_day,
            )

            # Calculate basic statistics
            total_appointments = appointments.count()
            completed_appointments = appointments.filter(
                status=Appointment.COMPLETED
            ).count()
            cancelled_appointments = appointments.filter(
                status=Appointment.CANCELLED
            ).count()
            pending_appointments = appointments.filter(
                status=Appointment.PENDING
            ).count()
            confirmed_appointments = appointments.filter(
                status=Appointment.CONFIRMED
            ).count()

            # Calculate financial metrics
            total_earnings = appointments.filter(
                status=Appointment.COMPLETED
            ).aggregate(total=Sum("consultation_fee"))["total"] or Decimal("0.00")

            potential_earnings = appointments.exclude(
                status=Appointment.CANCELLED
            ).aggregate(total=Sum("consultation_fee"))["total"] or Decimal("0.00")

            lost_earnings = appointments.filter(status=Appointment.CANCELLED).aggregate(
                total=Sum("consultation_fee")
            )["total"] or Decimal("0.00")

            # Calculate patient metrics
            unique_patients = appointments.values("patient_id").distinct().count()
            returning_patients = (
                appointments.filter(
                    patient_id__in=Appointment.objects.filter(
                        doctor_id=doctor_id,
                        appointment_date__lt=first_day,
                        status=Appointment.COMPLETED,
                    ).values_list("patient_id", flat=True)
                )
                .values("patient_id")
                .distinct()
                .count()
            )

            new_patients = unique_patients - returning_patients

            # Calculate efficiency metrics
            completion_rate = (
                completed_appointments / max(total_appointments, 1)
            ) * 100
            cancellation_rate = (
                cancelled_appointments / max(total_appointments, 1)
            ) * 100

            # Calculate daily averages
            working_days = appointments.values("appointment_date").distinct().count()
            avg_appointments_per_day = (
                total_appointments / max(working_days, 1) if working_days > 0 else 0
            )
            avg_earnings_per_day = (
                float(total_earnings) / max(working_days, 1) if working_days > 0 else 0
            )

            # Get busiest day
            busiest_day_data = (
                appointments.values("appointment_date")
                .annotate(count=Count("id"))
                .order_by("-count")
                .first()
            )

            busiest_day = {
                "date": (
                    busiest_day_data["appointment_date"] if busiest_day_data else None
                ),
                "appointment_count": (
                    busiest_day_data["count"] if busiest_day_data else 0
                ),
            }

            # Calculate time slot utilization
            time_slot_stats = {}
            if hasattr(doctor, "available_timeslots") and doctor.available_timeslots:
                for timeslot in doctor.available_timeslots:
                    slot_appointments = 0
                    try:
                        start_time = timeslot.split("-")[0]
                        hour, minute = start_time.split(":")
                        slot_appointments = appointments.filter(
                            appointment_time__hour=int(hour),
                            appointment_time__minute=int(minute),
                        ).count()
                    except (ValueError, IndexError):
                        pass

                    time_slot_stats[timeslot] = {
                        "appointments": slot_appointments,
                        "utilization_rate": (
                            (slot_appointments / max(working_days, 1)) * 100
                            if working_days > 0
                            else 0
                        ),
                    }

            return {
                "doctor_info": {
                    "id": doctor.id,
                    "name": doctor.full_name,
                    "license_number": getattr(doctor, "license_number", ""),
                    "consultation_fee": float(getattr(doctor, "consultation_fee", 0)),
                },
                "period": {
                    "year": year,
                    "month": month,
                    "month_name": calendar.month_name[month],
                    "first_day": first_day,
                    "last_day": last_day,
                    "total_days": (last_day - first_day).days + 1,
                    "working_days": working_days,
                },
                "appointment_stats": {
                    "total_appointments": total_appointments,
                    "completed_appointments": completed_appointments,
                    "cancelled_appointments": cancelled_appointments,
                    "pending_appointments": pending_appointments,
                    "confirmed_appointments": confirmed_appointments,
                    "completion_rate": round(completion_rate, 2),
                    "cancellation_rate": round(cancellation_rate, 2),
                },
                "financial_stats": {
                    "total_earnings": float(total_earnings),
                    "potential_earnings": float(potential_earnings),
                    "lost_earnings": float(lost_earnings),
                    "avg_earnings_per_appointment": float(
                        total_earnings / max(completed_appointments, 1)
                    ),
                    "avg_earnings_per_day": round(avg_earnings_per_day, 2),
                },
                "patient_stats": {
                    "unique_patients": unique_patients,
                    "new_patients": new_patients,
                    "returning_patients": returning_patients,
                    "patient_retention_rate": round(
                        (returning_patients / max(unique_patients, 1)) * 100, 2
                    ),
                },
                "performance_metrics": {
                    "avg_appointments_per_day": round(avg_appointments_per_day, 2),
                    "busiest_day": busiest_day,
                    "time_slot_utilization": time_slot_stats,
                },
            }

        except Exception as e:
            logger.error(f"Error calculating doctor monthly stats: {str(e)}")
            raise ReportGenerationError(
                f"Failed to calculate monthly statistics: {str(e)}"
            )

    @classmethod
    def generate_monthly_doctor_report(
        cls, doctor_id: int, year: int, month: int, force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate or retrieve monthly report for a doctor
        """
        try:
            # Check if report already exists
            existing_report = ReportSelector.get_doctor_monthly_report(
                doctor_id, year, month
            )

            if existing_report and not force_regenerate:
                logger.info(
                    f"Returning existing report for doctor {doctor_id}, {year}-{month}"
                )
                return {
                    "success": True,
                    "message": "Monthly report retrieved from database",
                    "report": existing_report.report_data,
                    "generated_at": existing_report.generated_at,
                    "from_cache": True,
                }

            # Generate new report
            logger.info(
                f"Generating new monthly report for doctor {doctor_id}, {year}-{month}"
            )

            report_data = cls.calculate_doctor_monthly_stats(doctor_id, year, month)

            # Save or update report in database
            monthly_report, created = MonthlyReport.objects.update_or_create(
                doctor_id=doctor_id,
                report_year=year,
                report_month=month,
                defaults={
                    "report_data": report_data,
                    "total_appointments": report_data["appointment_stats"][
                        "total_appointments"
                    ],
                    "total_patients": report_data["patient_stats"]["unique_patients"],
                    "total_earnings": Decimal(
                        str(report_data["financial_stats"]["total_earnings"])
                    ),
                    "generated_at": timezone.now(),
                },
            )

            action = "Generated" if created else "Updated"
            logger.info(
                f"{action} monthly report for doctor {doctor_id}, {year}-{month}"
            )

            return {
                "success": True,
                "message": f"Monthly report {action.lower()} successfully",
                "report": report_data,
                "generated_at": monthly_report.generated_at,
                "from_cache": False,
            }

        except ReportGenerationError as e:
            logger.error(f"Report generation error: {str(e)}")
            return {"success": False, "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error generating monthly report: {str(e)}")
            return {
                "success": False,
                "message": "Failed to generate monthly report due to server error",
            }

    @staticmethod
    def generate_system_monthly_report(year: int, month: int) -> Dict[str, Any]:
        """
        Generate system-wide monthly report for admin
        """
        try:
            first_day, last_day = ReportServices.get_month_date_range(year, month)

            # Get all appointments for the month
            monthly_appointments = Appointment.objects.filter(
                appointment_date__gte=first_day, appointment_date__lte=last_day
            )

            # Overall system statistics
            total_appointments = monthly_appointments.count()
            completed_appointments = monthly_appointments.filter(
                status=Appointment.COMPLETED
            ).count()
            cancelled_appointments = monthly_appointments.filter(
                status=Appointment.CANCELLED
            ).count()

            total_earnings = monthly_appointments.filter(
                status=Appointment.COMPLETED
            ).aggregate(total=Sum("consultation_fee"))["total"] or Decimal("0.00")

            unique_patients = (
                monthly_appointments.values("patient_id").distinct().count()
            )
            active_doctors = monthly_appointments.values("doctor_id").distinct().count()

            # Doctor performance rankings
            doctor_rankings = (
                monthly_appointments.filter(status=Appointment.COMPLETED)
                .values("doctor_id", "doctor__full_name")
                .annotate(
                    appointments_count=Count("id"),
                    earnings=Sum("consultation_fee"),
                    unique_patients=Count("patient_id", distinct=True),
                )
                .order_by("-earnings")[:10]
            )

            # Patient volume analysis
            patient_stats = (
                monthly_appointments.values("patient_id")
                .annotate(appointment_count=Count("id"))
                .aggregate(
                    avg_appointments_per_patient=Avg("appointment_count"),
                )
            )

            # Daily trends
            daily_trends = (
                monthly_appointments.values("appointment_date")
                .annotate(
                    appointment_count=Count("id"),
                    earnings=Sum(
                        "consultation_fee", filter=Q(status=Appointment.COMPLETED)
                    ),
                )
                .order_by("appointment_date")
            )

            # Status distribution
            status_distribution = {
                "completed": completed_appointments,
                "cancelled": cancelled_appointments,
                "pending": monthly_appointments.filter(
                    status=Appointment.PENDING
                ).count(),
                "confirmed": monthly_appointments.filter(
                    status=Appointment.CONFIRMED
                ).count(),
            }

            # Time slot analysis
            popular_time_slots = (
                monthly_appointments.extra(
                    select={"hour": "EXTRACT(hour FROM appointment_time)"}
                )
                .values("hour")
                .annotate(appointment_count=Count("id"))
                .order_by("-appointment_count")[:5]
            )

            # Calculate growth metrics (compare with previous month)
            prev_month = month - 1 if month > 1 else 12
            prev_year = year if month > 1 else year - 1
            prev_first_day, prev_last_day = ReportServices.get_month_date_range(
                prev_year, prev_month
            )

            prev_appointments = Appointment.objects.filter(
                appointment_date__gte=prev_first_day,
                appointment_date__lte=prev_last_day,
            )

            prev_total = prev_appointments.count()
            prev_earnings = prev_appointments.filter(
                status=Appointment.COMPLETED
            ).aggregate(total=Sum("consultation_fee"))["total"] or Decimal("0.00")

            appointment_growth = (
                (total_appointments - prev_total) / max(prev_total, 1)
            ) * 100
            earnings_growth = (
                (float(total_earnings) - float(prev_earnings))
                / max(float(prev_earnings), 1)
            ) * 100

            # User growth
            new_patients_this_month = User.objects.filter(
                user_type=UserType.PATIENT.value,
                created_at__date__gte=first_day,
                created_at__date__lte=last_day,
            ).count()

            new_doctors_this_month = User.objects.filter(
                user_type=UserType.DOCTOR.value,
                created_at__date__gte=first_day,
                created_at__date__lte=last_day,
            ).count()

            report_data = {
                "period": {
                    "year": year,
                    "month": month,
                    "month_name": calendar.month_name[month],
                    "first_day": first_day,
                    "last_day": last_day,
                },
                "overview": {
                    "total_appointments": total_appointments,
                    "completed_appointments": completed_appointments,
                    "cancelled_appointments": cancelled_appointments,
                    "total_earnings": float(total_earnings),
                    "unique_patients": unique_patients,
                    "active_doctors": active_doctors,
                    "completion_rate": (
                        completed_appointments / max(total_appointments, 1)
                    )
                    * 100,
                    "cancellation_rate": (
                        cancelled_appointments / max(total_appointments, 1)
                    )
                    * 100,
                },
                "growth_metrics": {
                    "appointment_growth_percent": round(appointment_growth, 2),
                    "earnings_growth_percent": round(earnings_growth, 2),
                    "new_patients_this_month": new_patients_this_month,
                    "new_doctors_this_month": new_doctors_this_month,
                },
                "doctor_rankings": [
                    {
                        "doctor_id": ranking["doctor_id"],
                        "doctor_name": ranking["doctor__full_name"],
                        "appointments": ranking["appointments_count"],
                        "earnings": float(ranking["earnings"] or 0),
                        "unique_patients": ranking["unique_patients"],
                    }
                    for ranking in doctor_rankings
                ],
                "patient_analytics": {
                    "avg_appointments_per_patient": round(
                        patient_stats["avg_appointments_per_patient"] or 0, 2
                    ),
                    "total_unique_patients": unique_patients,
                    "new_patients": new_patients_this_month,
                },
                "daily_trends": [
                    {
                        "date": trend["appointment_date"],
                        "appointments": trend["appointment_count"],
                        "earnings": float(trend["earnings"] or 0),
                    }
                    for trend in daily_trends
                ],
                "status_distribution": status_distribution,
                "popular_time_slots": [
                    {
                        "hour": f"{int(slot['hour'])}:00",
                        "appointment_count": slot["appointment_count"],
                    }
                    for slot in popular_time_slots
                ],
            }

            logger.info(f"Generated system monthly report for {year}-{month}")

            return {
                "success": True,
                "message": "System monthly report generated successfully",
                "report": report_data,
            }

        except Exception as e:
            logger.error(f"Error generating system monthly report: {str(e)}")
            return {
                "success": False,
                "message": "Failed to generate system monthly report",
            }

    @staticmethod
    def generate_doctor_annual_summary(doctor_id: int, year: int) -> Dict[str, Any]:
        """
        Generate annual summary report for a doctor
        """
        try:
            try:
                doctor = User.objects.get(id=doctor_id, user_type=UserType.DOCTOR.value)
            except User.DoesNotExist:
                return {"success": False, "message": "Doctor not found"}

            # Get all monthly reports for the year
            monthly_reports = ReportSelector.get_doctor_reports_by_year(doctor_id, year)

            if not monthly_reports:
                return {
                    "success": False,
                    "message": f"No monthly reports found for {year}",
                }

            # Aggregate annual statistics
            annual_stats = {
                "total_appointments": 0,
                "total_earnings": 0.0,
                "total_patients": 0,
                "monthly_breakdown": [],
            }

            monthly_earnings = []
            monthly_appointments = []

            for report in monthly_reports:
                data = report.report_data

                annual_stats["total_appointments"] += data["appointment_stats"][
                    "total_appointments"
                ]
                annual_stats["total_earnings"] += data["financial_stats"][
                    "total_earnings"
                ]
                annual_stats["total_patients"] += data["patient_stats"][
                    "unique_patients"
                ]

                monthly_breakdown = {
                    "month": data["period"]["month"],
                    "month_name": data["period"]["month_name"],
                    "appointments": data["appointment_stats"]["total_appointments"],
                    "earnings": data["financial_stats"]["total_earnings"],
                    "patients": data["patient_stats"]["unique_patients"],
                    "completion_rate": data["appointment_stats"]["completion_rate"],
                }

                annual_stats["monthly_breakdown"].append(monthly_breakdown)
                monthly_earnings.append(data["financial_stats"]["total_earnings"])
                monthly_appointments.append(
                    data["appointment_stats"]["total_appointments"]
                )

            # Calculate trends and averages
            avg_monthly_earnings = sum(monthly_earnings) / len(monthly_earnings)
            avg_monthly_appointments = sum(monthly_appointments) / len(
                monthly_appointments
            )

            # Find best and worst performing months
            best_earning_month = max(
                annual_stats["monthly_breakdown"], key=lambda x: x["earnings"]
            )
            worst_earning_month = min(
                annual_stats["monthly_breakdown"], key=lambda x: x["earnings"]
            )

            busiest_month = max(
                annual_stats["monthly_breakdown"], key=lambda x: x["appointments"]
            )
            quietest_month = min(
                annual_stats["monthly_breakdown"], key=lambda x: x["appointments"]
            )

            return {
                "success": True,
                "message": f"Annual summary generated for {year}",
                "doctor_info": {
                    "id": doctor.id,
                    "name": doctor.full_name,
                    "license_number": getattr(doctor, "license_number", ""),
                },
                "year": year,
                "summary": {
                    "total_appointments": annual_stats["total_appointments"],
                    "total_earnings": annual_stats["total_earnings"],
                    "unique_patients_served": annual_stats["total_patients"],
                    "avg_monthly_earnings": round(avg_monthly_earnings, 2),
                    "avg_monthly_appointments": round(avg_monthly_appointments, 2),
                    "months_with_data": len(monthly_reports),
                },
                "performance_highlights": {
                    "best_earning_month": best_earning_month,
                    "worst_earning_month": worst_earning_month,
                    "busiest_month": busiest_month,
                    "quietest_month": quietest_month,
                },
                "monthly_breakdown": annual_stats["monthly_breakdown"],
            }

        except Exception as e:
            logger.error(f"Error generating annual summary: {str(e)}")
            return {"success": False, "message": "Failed to generate annual summary"}

    @classmethod
    def bulk_generate_monthly_reports(
        cls, year: int, month: int, doctor_ids: List[int] = None
    ) -> Dict[str, Any]:
        """
        Generate monthly reports for multiple doctors (used by scheduler)
        """
        try:
            if doctor_ids is None:
                # Get all doctors who had appointments in the month
                first_day, last_day = cls.get_month_date_range(year, month)
                doctor_ids = (
                    Appointment.objects.filter(
                        appointment_date__gte=first_day, appointment_date__lte=last_day
                    )
                    .values_list("doctor_id", flat=True)
                    .distinct()
                )

            results = {
                "total_doctors": len(doctor_ids),
                "successful_reports": 0,
                "failed_reports": 0,
                "results": [],
            }

            for doctor_id in doctor_ids:
                try:
                    result = cls.generate_monthly_doctor_report(
                        doctor_id, year, month, force_regenerate=True
                    )

                    if result["success"]:
                        results["successful_reports"] += 1
                        status = "success"
                    else:
                        results["failed_reports"] += 1
                        status = "failed"

                    results["results"].append(
                        {
                            "doctor_id": doctor_id,
                            "status": status,
                            "message": result["message"],
                        }
                    )

                except Exception as e:
                    results["failed_reports"] += 1
                    results["results"].append(
                        {"doctor_id": doctor_id, "status": "failed", "message": str(e)}
                    )
                    logger.error(
                        f"Failed to generate report for doctor {doctor_id}: {str(e)}"
                    )

            logger.info(
                f"Bulk report generation completed: {results['successful_reports']} success, {results['failed_reports']} failed"
            )

            return {
                "success": True,
                "message": f"Generated {results['successful_reports']} reports, {results['failed_reports']} failed",
                "results": results,
            }

        except Exception as e:
            logger.error(f"Error in bulk report generation: {str(e)}")
            return {
                "success": False,
                "message": "Failed to perform bulk report generation",
            }

    @staticmethod
    def get_report_statistics() -> Dict[str, Any]:
        """
        Get report generation statistics for admin dashboard
        """
        try:
            total_reports = MonthlyReport.objects.count()

            # Reports by month
            recent_reports = (
                MonthlyReport.objects.values("report_year", "report_month")
                .annotate(report_count=Count("id"))
                .order_by("-report_year", "-report_month")[:12]
            )

            # Top performing doctors (by total earnings)
            top_doctors = (
                MonthlyReport.objects.values("doctor_id", "doctor__full_name")
                .annotate(
                    total_earnings=Sum("total_earnings"),
                    total_appointments=Sum("total_appointments"),
                    total_patients=Sum("total_patients"),
                )
                .order_by("-total_earnings")[:10]
            )

            # Latest generation activity
            latest_reports = MonthlyReport.objects.select_related("doctor").order_by(
                "-generated_at"
            )[:5]

            return {
                "success": True,
                "statistics": {
                    "total_reports_generated": total_reports,
                    "recent_report_activity": [
                        {
                            "year": report["report_year"],
                            "month": report["report_month"],
                            "month_name": calendar.month_name[report["report_month"]],
                            "report_count": report["report_count"],
                        }
                        for report in recent_reports
                    ],
                    "top_performing_doctors": [
                        {
                            "doctor_id": doctor["doctor_id"],
                            "doctor_name": doctor["doctor__full_name"],
                            "total_earnings": float(doctor["total_earnings"] or 0),
                            "total_appointments": doctor["total_appointments"] or 0,
                            "total_patients": doctor["total_patients"] or 0,
                        }
                        for doctor in top_doctors
                    ],
                    "latest_generated_reports": [
                        {
                            "doctor_name": report.doctor.full_name,
                            "period": f"{calendar.month_name[report.report_month]} {report.report_year}",
                            "generated_at": report.generated_at,
                        }
                        for report in latest_reports
                    ],
                },
            }

        except Exception as e:
            logger.error(f"Error getting report statistics: {str(e)}")
            return {"success": False, "message": "Failed to retrieve report statistics"}

    @staticmethod
    def get_comparative_analysis(
        doctor_ids: List[int], year: int, month: int = None
    ) -> Dict[str, Any]:
        """
        Generate comparative analysis between multiple doctors
        """
        try:
            if month:
                # Monthly comparison
                reports = []
                for doctor_id in doctor_ids:
                    report = ReportSelector.get_doctor_monthly_report(
                        doctor_id, year, month
                    )
                    if report:
                        reports.append(report)

                comparison_data = []
                for report in reports:
                    data = report.report_data
                    comparison_data.append(
                        {
                            "doctor_id": report.doctor_id,
                            "doctor_name": report.doctor.full_name,
                            "appointments": data["appointment_stats"][
                                "total_appointments"
                            ],
                            "earnings": data["financial_stats"]["total_earnings"],
                            "patients": data["patient_stats"]["unique_patients"],
                            "completion_rate": data["appointment_stats"][
                                "completion_rate"
                            ],
                            "period": f"{calendar.month_name[month]} {year}",
                        }
                    )

            else:
                # Annual comparison
                comparison_data = []
                for doctor_id in doctor_ids:
                    annual_summary = ReportServices.generate_doctor_annual_summary(
                        doctor_id, year
                    )
                    if annual_summary["success"]:
                        summary = annual_summary["summary"]
                        comparison_data.append(
                            {
                                "doctor_id": doctor_id,
                                "doctor_name": annual_summary["doctor_info"]["name"],
                                "appointments": summary["total_appointments"],
                                "earnings": summary["total_earnings"],
                                "patients": summary["unique_patients_served"],
                                "avg_monthly_earnings": summary["avg_monthly_earnings"],
                                "months_active": summary["months_with_data"],
                                "period": f"Year {year}",
                            }
                        )

            # Sort by earnings
            comparison_data.sort(key=lambda x: x["earnings"], reverse=True)

            # Calculate rankings and percentages
            total_earnings = sum(doc["earnings"] for doc in comparison_data)
            total_appointments = sum(doc["appointments"] for doc in comparison_data)

            for i, doc in enumerate(comparison_data):
                doc["rank"] = i + 1
                doc["earnings_percentage"] = (
                    doc["earnings"] / max(total_earnings, 1)
                ) * 100
                doc["appointments_percentage"] = (
                    doc["appointments"] / max(total_appointments, 1)
                ) * 100

            return {
                "success": True,
                "message": "Comparative analysis generated successfully",
                "period": (
                    f"{calendar.month_name[month]} {year}" if month else f"Year {year}"
                ),
                "doctors_compared": len(comparison_data),
                "comparison": comparison_data,
                "totals": {
                    "total_earnings": total_earnings,
                    "total_appointments": total_appointments,
                    "avg_earnings_per_doctor": total_earnings
                    / max(len(comparison_data), 1),
                    "avg_appointments_per_doctor": total_appointments
                    / max(len(comparison_data), 1),
                },
            }

        except Exception as e:
            logger.error(f"Error generating comparative analysis: {str(e)}")
            return {
                "success": False,
                "message": "Failed to generate comparative analysis",
            }

    @staticmethod
    def get_earnings_forecast(doctor_id: int, months_ahead: int = 3) -> Dict[str, Any]:
        """
        Generate earnings forecast based on historical data
        """
        try:
            # Get last 6 months of data for trend analysis
            current_date = timezone.now().date()
            trends = ReportSelector.get_earnings_trends(doctor_id, months=6)

            if len(trends) < 3:
                return {
                    "success": False,
                    "message": "Insufficient historical data for forecasting",
                }

            # Simple linear trend calculation
            recent_earnings = [trend["earnings"] for trend in trends[-3:]]
            avg_earnings = sum(recent_earnings) / len(recent_earnings)

            # Calculate growth trend
            if len(recent_earnings) >= 2:
                growth_rate = (recent_earnings[-1] - recent_earnings[0]) / max(
                    recent_earnings[0], 1
                )
            else:
                growth_rate = 0

            # Generate forecast
            forecast = []
            for i in range(1, months_ahead + 1):
                next_month = current_date.month + i
                next_year = current_date.year

                if next_month > 12:
                    next_month = next_month - 12
                    next_year += 1

                projected_earnings = avg_earnings * (
                    1 + growth_rate * i * 0.1
                )  # Dampen growth

                forecast.append(
                    {
                        "year": next_year,
                        "month": next_month,
                        "month_name": calendar.month_name[next_month],
                        "projected_earnings": round(projected_earnings, 2),
                        "confidence": max(90 - i * 10, 50),  # Decreasing confidence
                    }
                )

            return {
                "success": True,
                "message": "Earnings forecast generated successfully",
                "doctor_id": doctor_id,
                "historical_data": trends,
                "current_avg_monthly": round(avg_earnings, 2),
                "growth_rate": round(growth_rate * 100, 2),
                "forecast": forecast,
            }

        except Exception as e:
            logger.error(f"Error generating earnings forecast: {str(e)}")
            return {"success": False, "message": "Failed to generate earnings forecast"}

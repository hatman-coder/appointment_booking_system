import calendar
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from django.db.models import Avg, Count, Q, QuerySet, Sum
from django.utils import timezone

from apps.account.models import User
from apps.appointment.models import Appointment

from .models import MonthlyReport


class ReportSelector:
    """Selector class for report-related queries"""

    @staticmethod
    def get_monthly_report_by_id(report_id: int) -> Optional[MonthlyReport]:
        """Get monthly report by ID"""
        try:
            return MonthlyReport.objects.select_related("doctor").get(id=report_id)
        except MonthlyReport.DoesNotExist:
            return None

    @staticmethod
    def get_doctor_monthly_report(
        doctor_id: int, year: int, month: int
    ) -> Optional[MonthlyReport]:
        """Get monthly report for specific doctor, month, and year - used by services"""
        try:
            return MonthlyReport.objects.select_related("doctor").get(
                doctor_id=doctor_id, report_year=year, report_month=month
            )
        except MonthlyReport.DoesNotExist:
            return None

    @staticmethod
    def get_monthly_report(
        doctor_id: int, month: int, year: int
    ) -> Optional[MonthlyReport]:
        """Get monthly report for specific doctor, month, and year - legacy method"""
        return ReportSelector.get_doctor_monthly_report(doctor_id, year, month)

    @staticmethod
    def get_all_monthly_reports() -> QuerySet:
        """Get all monthly reports"""
        return MonthlyReport.objects.select_related("doctor").order_by(
            "-report_year", "-report_month"
        )

    @staticmethod
    def get_doctor_monthly_reports(doctor_id: int) -> QuerySet:
        """Get all monthly reports for a specific doctor"""
        return (
            MonthlyReport.objects.filter(doctor_id=doctor_id)
            .select_related("doctor")
            .order_by("-report_year", "-report_month")
        )

    @staticmethod
    def get_doctor_reports_by_year(doctor_id: int, year: int) -> QuerySet:
        """Get all monthly reports for a specific doctor and year - used by services"""
        return (
            MonthlyReport.objects.filter(doctor_id=doctor_id, report_year=year)
            .select_related("doctor")
            .order_by("report_month")
        )

    @staticmethod
    def get_monthly_reports_by_period(month: int, year: int) -> QuerySet:
        """Get all monthly reports for a specific month/year"""
        return (
            MonthlyReport.objects.filter(report_month=month, report_year=year)
            .select_related("doctor")
            .order_by("-total_earnings")
        )

    @staticmethod
    def get_top_earning_doctors(
        month: int = None, year: int = None, limit: int = 10
    ) -> QuerySet:
        """Get top earning doctors for a period"""
        queryset = MonthlyReport.objects.select_related("doctor")

        if month and year:
            queryset = queryset.filter(report_month=month, report_year=year)
        elif year:
            queryset = queryset.filter(report_year=year)

        return queryset.order_by("-total_earnings")[:limit]

    @staticmethod
    def generate_appointment_statistics(
        start_date: date, end_date: date
    ) -> Dict[str, Any]:
        """Generate appointment statistics for date range"""
        appointments = Appointment.objects.filter(
            appointment_date__gte=start_date, appointment_date__lte=end_date
        )

        total_appointments = appointments.count()
        completed_appointments = appointments.filter(
            status=Appointment.COMPLETED
        ).count()
        cancelled_appointments = appointments.filter(
            status=Appointment.CANCELLED
        ).count()
        pending_appointments = appointments.filter(status=Appointment.PENDING).count()
        confirmed_appointments = appointments.filter(
            status=Appointment.CONFIRMED
        ).count()

        # Appointments by doctor
        doctor_stats = (
            appointments.values("doctor__full_name")
            .annotate(
                count=Count("id"),
                completed=Count("id", filter=Q(status=Appointment.COMPLETED)),
                earnings=Sum(
                    "consultation_fee", filter=Q(status=Appointment.COMPLETED)
                ),
            )
            .order_by("-count")
        )

        # Daily breakdown
        daily_stats = (
            appointments.values("appointment_date")
            .annotate(count=Count("id"))
            .order_by("appointment_date")
        )

        return {
            "period": f"{start_date} to {end_date}",
            "total_appointments": total_appointments,
            "completed_appointments": completed_appointments,
            "cancelled_appointments": cancelled_appointments,
            "pending_appointments": pending_appointments,
            "confirmed_appointments": confirmed_appointments,
            "completion_rate": (
                (completed_appointments / total_appointments * 100)
                if total_appointments > 0
                else 0
            ),
            "doctor_statistics": list(doctor_stats),
            "daily_breakdown": list(daily_stats),
        }

    @staticmethod
    def generate_doctor_performance_report(
        doctor_id: int, start_date: date, end_date: date
    ) -> Dict[str, Any]:
        """Generate performance report for specific doctor"""
        appointments = Appointment.objects.filter(
            doctor_id=doctor_id,
            appointment_date__gte=start_date,
            appointment_date__lte=end_date,
        )

        total_appointments = appointments.count()
        completed = appointments.filter(status=Appointment.COMPLETED).count()
        cancelled = appointments.filter(status=Appointment.CANCELLED).count()
        pending = appointments.filter(status=Appointment.PENDING).count()
        confirmed = appointments.filter(status=Appointment.CONFIRMED).count()

        # Calculate earnings from actual appointment fees
        total_earnings = (
            appointments.filter(status=Appointment.COMPLETED).aggregate(
                total=Sum("consultation_fee")
            )["total"]
            or 0
        )

        # Patient count (unique patients)
        unique_patients = appointments.values("patient").distinct().count()

        # Get doctor info
        try:
            doctor = User.objects.get(id=doctor_id, user_type=UserType.DOCTOR.value)
            doctor_name = doctor.full_name
        except User.DoesNotExist:
            doctor_name = "Unknown Doctor"

        return {
            "doctor_name": doctor_name,
            "doctor_id": doctor_id,
            "period": f"{start_date} to {end_date}",
            "total_appointments": total_appointments,
            "completed_appointments": completed,
            "cancelled_appointments": cancelled,
            "pending_appointments": pending,
            "confirmed_appointments": confirmed,
            "unique_patients": unique_patients,
            "total_earnings": float(total_earnings),
            "completion_rate": (
                (completed / total_appointments * 100) if total_appointments > 0 else 0
            ),
            "cancellation_rate": (
                (cancelled / total_appointments * 100) if total_appointments > 0 else 0
            ),
        }

    @staticmethod
    def get_system_overview() -> Dict[str, Any]:
        """Get system-wide statistics"""
        total_users = User.objects.count()
        total_doctors = User.objects.filter(user_type=UserType.DOCTOR.value).count()
        total_patients = User.objects.filter(user_type=UserType.PATIENT.value).count()

        # Active doctors (those with appointments in last 30 days)
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        active_doctors = (
            User.objects.filter(
                user_type=UserType.DOCTOR.value,
                doctor_appointments__appointment_date__gte=thirty_days_ago,
            )
            .distinct()
            .count()
        )

        today = timezone.now().date()
        today_appointments = Appointment.objects.filter(appointment_date=today).count()

        this_month = today.replace(day=1)
        monthly_appointments = Appointment.objects.filter(
            appointment_date__gte=this_month
        ).count()

        # Recent activity
        recent_appointments = Appointment.objects.select_related(
            "patient", "doctor"
        ).order_by("-created_at")[:10]

        return {
            "total_users": total_users,
            "total_doctors": total_doctors,
            "total_patients": total_patients,
            "active_doctors": active_doctors,
            "today_appointments": today_appointments,
            "monthly_appointments": monthly_appointments,
            "recent_appointments": recent_appointments,
        }

    @staticmethod
    def get_reports_with_pagination(
        page: int = 1,
        limit: int = 20,
        doctor_id: int = None,
        year: int = None,
        month: int = None,
    ) -> Dict[str, Any]:
        """Get reports with pagination and filters"""
        from django.core.paginator import Paginator

        queryset = MonthlyReport.objects.select_related("doctor").all()

        # Apply filters
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        if year:
            queryset = queryset.filter(report_year=year)
        if month:
            queryset = queryset.filter(report_month=month)

        queryset = queryset.order_by("-report_year", "-report_month")

        paginator = Paginator(queryset, limit)
        reports_page = paginator.get_page(page)

        reports_data = []
        for report in reports_page:
            reports_data.append(
                {
                    "id": report.id,
                    "doctor_id": report.doctor_id,
                    "doctor_name": report.doctor.full_name,
                    "year": report.report_year,
                    "month": report.report_month,
                    "month_name": (
                        report.get_month_display()
                        if hasattr(report, "get_month_display")
                        else f"Month {report.report_month}"
                    ),
                    "total_appointments": report.total_appointments,
                    "total_patients": report.total_patients,
                    "total_earnings": float(report.total_earnings),
                    "generated_at": report.generated_at,
                }
            )

        return {
            "reports": reports_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total_pages": paginator.num_pages,
                "total_count": paginator.count,
                "has_next": reports_page.has_next(),
                "has_previous": reports_page.has_previous(),
            },
        }

    @staticmethod
    def get_earnings_trends(
        doctor_id: int = None, months: int = 12
    ) -> List[Dict[str, Any]]:
        """Get earnings trends for the last N months"""
        end_date = timezone.now().date()
        start_date = end_date.replace(day=1) - timedelta(days=months * 32)

        queryset = MonthlyReport.objects.filter(
            report_year__gte=start_date.year,
            report_month__gte=(
                start_date.month if start_date.year == end_date.year else 1
            ),
        )

        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)

        # Group by year and month
        trends = []
        if doctor_id:
            # Individual doctor trends
            reports = queryset.order_by("report_year", "report_month")
            for report in reports:
                trends.append(
                    {
                        "year": report.report_year,
                        "month": report.report_month,
                        "earnings": float(report.total_earnings),
                        "appointments": report.total_appointments,
                        "patients": report.total_patients,
                    }
                )
        else:
            # System-wide trends
            monthly_totals = (
                queryset.values("report_year", "report_month")
                .annotate(
                    total_earnings=Sum("total_earnings"),
                    total_appointments=Sum("total_appointments"),
                    total_patients=Sum("total_patients"),
                )
                .order_by("report_year", "report_month")
            )

            for total in monthly_totals:
                trends.append(
                    {
                        "year": total["report_year"],
                        "month": total["report_month"],
                        "earnings": float(total["total_earnings"] or 0),
                        "appointments": total["total_appointments"] or 0,
                        "patients": total["total_patients"] or 0,
                    }
                )

        return trends

    @staticmethod
    def get_doctor_comparison_stats(
        year: int, month: int = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get doctor performance comparison for ranking"""
        queryset = MonthlyReport.objects.filter(report_year=year)

        if month:
            queryset = queryset.filter(report_month=month)

        if month:
            # Single month comparison
            doctors = queryset.select_related("doctor").order_by("-total_earnings")[
                :limit
            ]

            comparison_data = []
            for report in doctors:
                comparison_data.append(
                    {
                        "doctor_id": report.doctor_id,
                        "doctor_name": report.doctor.full_name,
                        "earnings": float(report.total_earnings),
                        "appointments": report.total_appointments,
                        "patients": report.total_patients,
                        "period": f"{report.report_month}/{report.report_year}",
                    }
                )
        else:
            # Annual comparison
            annual_stats = (
                queryset.values("doctor_id", "doctor__full_name")
                .annotate(
                    total_earnings=Sum("total_earnings"),
                    total_appointments=Sum("total_appointments"),
                    total_patients=Sum("total_patients"),
                    months_active=Count("id"),
                )
                .order_by("-total_earnings")[:limit]
            )

            comparison_data = []
            for stats in annual_stats:
                comparison_data.append(
                    {
                        "doctor_id": stats["doctor_id"],
                        "doctor_name": stats["doctor__full_name"],
                        "earnings": float(stats["total_earnings"] or 0),
                        "appointments": stats["total_appointments"] or 0,
                        "patients": stats["total_patients"] or 0,
                        "months_active": stats["months_active"],
                        "avg_monthly_earnings": float(stats["total_earnings"] or 0)
                        / max(stats["months_active"], 1),
                        "period": f"Year {year}",
                    }
                )

        return comparison_data

    @staticmethod
    def get_report_summary_stats() -> Dict[str, Any]:
        """Get summary statistics about report generation"""
        total_reports = MonthlyReport.objects.count()

        # Latest report generation
        latest_report = MonthlyReport.objects.order_by("-generated_at").first()

        # Reports by year
        yearly_counts = (
            MonthlyReport.objects.values("report_year")
            .annotate(count=Count("id"))
            .order_by("-report_year")
        )

        # Total system earnings tracked
        total_earnings = (
            MonthlyReport.objects.aggregate(total=Sum("total_earnings"))["total"] or 0
        )

        # Doctor participation
        doctors_with_reports = (
            MonthlyReport.objects.values("doctor_id").distinct().count()
        )

        return {
            "total_reports": total_reports,
            "latest_report_date": latest_report.generated_at if latest_report else None,
            "yearly_distribution": list(yearly_counts),
            "total_earnings_tracked": float(total_earnings),
            "doctors_with_reports": doctors_with_reports,
        }

    # Missing methods needed by views
    @staticmethod
    def get_doctor_reports_with_pagination(
        doctor_id: int, page: int, limit: int, year: int = None
    ) -> Dict[str, Any]:
        """Get doctor reports with pagination - used by views"""
        from django.core.paginator import Paginator

        queryset = MonthlyReport.objects.filter(doctor_id=doctor_id)

        if year:
            queryset = queryset.filter(report_year=year)

        queryset = queryset.select_related("doctor").order_by(
            "-report_year", "-report_month"
        )

        paginator = Paginator(queryset, limit)
        reports_page = paginator.get_page(page)

        reports_data = []
        for report in reports_page:
            reports_data.append(
                {
                    "id": report.id,
                    "year": report.report_year,
                    "month": report.report_month,
                    "month_name": calendar.month_name[report.report_month],
                    "total_appointments": report.total_appointments,
                    "total_patients": report.total_patients,
                    "total_earnings": float(report.total_earnings),
                    "generated_at": report.generated_at,
                }
            )

        return {
            "reports": reports_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total_pages": paginator.num_pages,
                "total_count": paginator.count,
                "has_next": reports_page.has_next(),
                "has_previous": reports_page.has_previous(),
            },
        }

    @staticmethod
    def get_patient_report_summary(patient_id: int) -> Dict[str, Any]:
        """Get patient report summary for dashboard - used by views"""
        from apps.appointment.models import Appointment

        # Get patient's appointment statistics
        appointments = Appointment.objects.filter(patient_id=patient_id)

        total_appointments = appointments.count()
        completed = appointments.filter(status=Appointment.COMPLETED).count()
        cancelled = appointments.filter(status=Appointment.CANCELLED).count()
        pending = appointments.filter(status=Appointment.PENDING).count()

        # Total spent
        total_spent = (
            appointments.filter(status=Appointment.COMPLETED).aggregate(
                total=Sum("consultation_fee")
            )["total"]
            or 0
        )

        # Recent appointments
        recent_appointments = appointments.select_related("doctor").order_by(
            "-appointment_date"
        )[:5]

        # Monthly trend (last 6 months)
        from django.utils import timezone
        from datetime import timedelta

        six_months_ago = timezone.now().date() - timedelta(days=180)
        monthly_trend = (
            appointments.filter(appointment_date__gte=six_months_ago)
            .extra(
                select={
                    "month": "EXTRACT(month FROM appointment_date)",
                    "year": "EXTRACT(year FROM appointment_date)",
                }
            )
            .values("month", "year")
            .annotate(count=Count("id"))
            .order_by("year", "month")
        )

        return {
            "total_appointments": total_appointments,
            "completed_appointments": completed,
            "cancelled_appointments": cancelled,
            "pending_appointments": pending,
            "total_spent": float(total_spent),
            "recent_appointments": [
                {
                    "id": apt.id,
                    "doctor_name": apt.doctor.full_name,
                    "appointment_date": apt.appointment_date,
                    "status": apt.status,
                    "consultation_fee": float(apt.consultation_fee),
                }
                for apt in recent_appointments
            ],
            "monthly_trend": list(monthly_trend),
        }

    @staticmethod
    def get_doctor_recent_reports(doctor_id: int, months: int = 6) -> QuerySet:
        """Get doctor's recent reports - used by views"""
        return (
            MonthlyReport.objects.filter(doctor_id=doctor_id)
            .select_related("doctor")
            .order_by("-report_year", "-report_month")[:months]
        )

    @staticmethod
    def get_doctor_available_report_periods(doctor_id: int) -> List[Dict[str, Any]]:
        """Get available report periods for a doctor - used by views"""
        periods = (
            MonthlyReport.objects.filter(doctor_id=doctor_id)
            .values("report_year", "report_month")
            .order_by("-report_year", "-report_month")
        )

        available_periods = []
        for period in periods:
            available_periods.append(
                {
                    "year": period["report_year"],
                    "month": period["report_month"],
                    "month_name": calendar.month_name[period["report_month"]],
                    "display_name": f"{calendar.month_name[period['report_month']]} {period['report_year']}",
                }
            )

        return available_periods

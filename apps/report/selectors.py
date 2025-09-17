from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from django.db.models import Avg, Count, Q, QuerySet, Sum
from django.utils import timezone

from apps.account.models import Doctor
from apps.appointment.models import Appointment

from .models import AppointmentReminder, MonthlyReport


class ReportSelector:
    """Selector class for report-related queries"""

    @staticmethod
    def get_monthly_report_by_id(report_id: int) -> Optional[MonthlyReport]:
        """Get monthly report by ID"""
        try:
            return MonthlyReport.objects.select_related("doctor__user").get(
                id=report_id
            )
        except MonthlyReport.DoesNotExist:
            return None

    @staticmethod
    def get_monthly_report(
        doctor_id: int, month: int, year: int
    ) -> Optional[MonthlyReport]:
        """Get monthly report for specific doctor, month, and year"""
        try:
            return MonthlyReport.objects.select_related("doctor__user").get(
                doctor_id=doctor_id, month=month, year=year
            )
        except MonthlyReport.DoesNotExist:
            return None

    @staticmethod
    def get_all_monthly_reports() -> QuerySet:
        """Get all monthly reports"""
        return MonthlyReport.objects.select_related("doctor__user").order_by(
            "-year", "-month"
        )

    @staticmethod
    def get_doctor_monthly_reports(doctor_id: int) -> QuerySet:
        """Get all monthly reports for a specific doctor"""
        return (
            MonthlyReport.objects.filter(doctor_id=doctor_id)
            .select_related("doctor__user")
            .order_by("-year", "-month")
        )

    @staticmethod
    def get_monthly_reports_by_period(month: int, year: int) -> QuerySet:
        """Get all monthly reports for a specific month/year"""
        return (
            MonthlyReport.objects.filter(month=month, year=year)
            .select_related("doctor__user")
            .order_by("-total_earnings")
        )

    @staticmethod
    def get_top_earning_doctors(
        month: int = None, year: int = None, limit: int = 10
    ) -> QuerySet:
        """Get top earning doctors for a period"""
        queryset = MonthlyReport.objects.select_related("doctor__user")

        if month and year:
            queryset = queryset.filter(month=month, year=year)
        elif year:
            queryset = queryset.filter(year=year)

        return queryset.order_by("-total_earnings")[:limit]

    @staticmethod
    def get_appointment_reminders() -> QuerySet:
        """Get all appointment reminders"""
        return AppointmentReminder.objects.select_related(
            "appointment__patient__user", "appointment__doctor__user"
        ).order_by("-created_at")

    @staticmethod
    def get_pending_reminders() -> QuerySet:
        """Get reminders that haven't been sent"""
        return AppointmentReminder.objects.filter(reminder_sent=False).select_related(
            "appointment__patient__user", "appointment__doctor__user"
        )

    @staticmethod
    def get_sent_reminders(date_from: date = None, date_to: date = None) -> QuerySet:
        """Get reminders that have been sent"""
        queryset = AppointmentReminder.objects.filter(
            reminder_sent=True
        ).select_related("appointment__patient__user", "appointment__doctor__user")

        if date_from:
            queryset = queryset.filter(sent_at__gte=date_from)

        if date_to:
            queryset = queryset.filter(sent_at__lte=date_to)

        return queryset.order_by("-sent_at")

    @staticmethod
    def generate_appointment_statistics(
        start_date: date, end_date: date
    ) -> Dict[str, Any]:
        """Generate appointment statistics for date range"""
        appointments = Appointment.objects.filter(
            appointment_date__gte=start_date, appointment_date__lte=end_date
        )

        total_appointments = appointments.count()
        completed_appointments = appointments.filter(status="completed").count()
        cancelled_appointments = appointments.filter(status="cancelled").count()

        # Appointments by doctor
        doctor_stats = (
            appointments.values("doctor__user__full_name")
            .annotate(
                count=Count("id"),
                completed=Count("id", filter=Q(status="completed")),
                earnings=Sum("doctor__consultation_fee", filter=Q(status="completed")),
            )
            .order_by("-count")
        )

        # Daily breakdown
        daily_stats = (
            appointments.extra(select={"day": "date(appointment_date)"})
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )

        return {
            "period": f"{start_date} to {end_date}",
            "total_appointments": total_appointments,
            "completed_appointments": completed_appointments,
            "cancelled_appointments": cancelled_appointments,
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
        completed = appointments.filter(status="completed").count()
        cancelled = appointments.filter(status="cancelled").count()
        pending = appointments.filter(status="pending").count()

        # Calculate earnings
        doctor = Doctor.objects.get(id=doctor_id)
        total_earnings = completed * doctor.consultation_fee

        # Patient count (unique patients)
        unique_patients = appointments.values("patient").distinct().count()

        return {
            "doctor_name": doctor.user.full_name,
            "period": f"{start_date} to {end_date}",
            "total_appointments": total_appointments,
            "completed_appointments": completed,
            "cancelled_appointments": cancelled,
            "pending_appointments": pending,
            "unique_patients": unique_patients,
            "total_earnings": total_earnings,
            "completion_rate": (
                (completed / total_appointments * 100) if total_appointments > 0 else 0
            ),
        }

    @staticmethod
    def get_system_overview() -> Dict[str, Any]:
        """Get system-wide statistics"""
        from apps.account.models import User

        total_users = User.objects.count()
        total_doctors = Doctor.objects.count()
        total_patients = User.objects.filter(user_type="patient").count()
        active_doctors = Doctor.objects.filter(is_available=True).count()

        today = timezone.now().date()
        today_appointments = Appointment.objects.filter(appointment_date=today).count()

        this_month = today.replace(day=1)
        monthly_appointments = Appointment.objects.filter(
            appointment_date__gte=this_month
        ).count()

        # Recent activity
        recent_appointments = Appointment.objects.select_related(
            "patient__user", "doctor__user"
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

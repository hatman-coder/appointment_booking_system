from typing import Optional

from django.db.models import QuerySet

from .models import MonthlyReport


class ReportSelector:
    @staticmethod
    def get_monthly_report(
        doctor_id: int, month: int, year: int
    ) -> Optional[MonthlyReport]:
        try:
            return MonthlyReport.objects.select_related("doctor__user").get(
                doctor_id=doctor_id, month=month, year=year
            )
        except MonthlyReport.DoesNotExist:
            return None

    @staticmethod
    def get_all_monthly_reports() -> QuerySet:
        return MonthlyReport.objects.select_related("doctor__user").order_by(
            "-year", "-month"
        )

    @staticmethod
    def get_doctor_monthly_reports(doctor_id: int) -> QuerySet:
        return (
            MonthlyReport.objects.filter(doctor_id=doctor_id)
            .select_related("doctor__user")
            .order_by("-year", "-month")
        )

from django.db import transaction
from django.db.models import Count, Sum
from apps.appointment.models import Appointment
from apps.account.models import Doctor
from .models import MonthlyReport
from .selectors import ReportSelector
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class ReportService:
    @staticmethod
    def generate_monthly_report(doctor_id: int, month: int, year: int) -> MonthlyReport:
        try:
            with transaction.atomic():
                # Get or create monthly report
                report, created = MonthlyReport.objects.get_or_create(
                    doctor_id=doctor_id, month=month, year=year
                )

                # Calculate statistics from appointments
                appointments = Appointment.objects.filter(
                    doctor_id=doctor_id,
                    appointment_date__month=month,
                    appointment_date__year=year,
                    status="completed",
                )

                doctor = Doctor.objects.get(id=doctor_id)

                # Update report data
                report.total_appointments = appointments.count()
                report.total_patients = (
                    appointments.values("patient").distinct().count()
                )
                report.total_earnings = (
                    report.total_appointments * doctor.consultation_fee
                )
                report.save()

                logger.info(
                    f"Monthly report generated for doctor {doctor_id}, {month}/{year}"
                )
                return report

        except Exception as e:
            logger.error(f"Failed to generate monthly report: {str(e)}")
            raise

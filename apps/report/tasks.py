from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from apps.appointment.models import Appointment
from .services import ReportService
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_appointment_reminders():
    """Send appointment reminders 24 hours before"""
    tomorrow = timezone.now().date() + timedelta(days=1)
    appointments = Appointment.objects.filter(
        appointment_date=tomorrow, status="confirmed"
    ).select_related("patient__user", "doctor__user")

    for appointment in appointments:
        try:
            send_mail(
                subject="Appointment Reminder",
                message=f"You have an appointment with Dr. {appointment.doctor.user.full_name} "
                f"on {appointment.appointment_date} at {appointment.appointment_time}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[appointment.patient.user.email],
                fail_silently=False,
            )
            logger.info(f"Reminder sent for appointment {appointment.id}")
        except Exception as e:
            logger.error(
                f"Failed to send reminder for appointment {appointment.id}: {str(e)}"
            )


@shared_task
def generate_monthly_reports():
    """Generate monthly reports for all doctors"""
    from apps.accounts.models import Doctor

    current_date = timezone.now().date()
    # Generate for previous month
    if current_date.month == 1:
        month, year = 12, current_date.year - 1
    else:
        month, year = current_date.month - 1, current_date.year

    doctors = Doctor.objects.all()

    for doctor in doctors:
        try:
            ReportService.generate_monthly_report(doctor.id, month, year)
            logger.info(f"Monthly report generated for doctor {doctor.id}")
        except Exception as e:
            logger.error(f"Failed to generate report for doctor {doctor.id}: {str(e)}")

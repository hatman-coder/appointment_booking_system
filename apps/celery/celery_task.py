from celery import shared_task
from apps.scheduler.tasks import (
    send_appointment_reminders as _send_reminders,
    generate_monthly_reports as _generate_reports,
    cleanup_old_data as _cleanup_data,
    system_health_check as _health_check,
    generate_weekly_summary_report as _weekly_summary,
)


@shared_task(bind=True, max_retries=3)
def send_appointment_reminders(self):
    """Celery task for sending appointment reminders"""
    try:
        result = _send_reminders()
        return result
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))


@shared_task(bind=True, max_retries=2)
def generate_monthly_reports(self):
    """Celery task for generating monthly reports"""
    try:
        result = _generate_reports()
        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes


@shared_task
def cleanup_old_data():
    """Celery task for data cleanup"""
    return _cleanup_data()


@shared_task
def system_health_check():
    """Celery task for system health check"""
    return _health_check()


@shared_task
def generate_weekly_summary_report():
    """Celery task for weekly summary report"""
    return _weekly_summary()

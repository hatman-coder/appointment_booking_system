from celery import Celery
from django.conf import settings
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "appointment_system.settings")

app = Celery("appointment_system")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    "send-appointment-reminders": {
        "task": "apps.reports.tasks.send_appointment_reminders",
        "schedule": 3600.0,  # Run every hour
    },
    "generate-monthly-reports": {
        "task": "apps.reports.tasks.generate_monthly_reports",
        "schedule": 86400.0,  # Run daily
    },
}

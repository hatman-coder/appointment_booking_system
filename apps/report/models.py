from core.models import BaseModel
from django.db import models

from apps.account.models import Doctor


class MonthlyReport(BaseModel):
    doctor = models.ForeignKey(
        Doctor, on_delete=models.CASCADE, related_name="monthly_reports"
    )
    month = models.PositiveIntegerField()
    year = models.PositiveIntegerField()
    total_patients = models.PositiveIntegerField(default=0)
    total_appointments = models.PositiveIntegerField(default=0)
    total_earnings = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "monthly_reports"
        unique_together = ["doctor", "month", "year"]

    def __str__(self):
        return f"{self.doctor.user.full_name} - {self.month}/{self.year}"


class AppointmentReminder(BaseModel):
    appointment = models.OneToOneField(
        "appointments.Appointment", on_delete=models.CASCADE, related_name="reminder"
    )
    reminder_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "appointment_reminders"

    def __str__(self):
        return f"Reminder for {self.appointment}"

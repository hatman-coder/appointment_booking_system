from core.enum import AppointmentStatus
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.account.models import Doctor, Patient


class Appointment(models.Model):

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="appointments"
    )
    doctor = models.ForeignKey(
        Doctor, on_delete=models.CASCADE, related_name="appointments"
    )
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(
        max_length=15, choices=AppointmentStatus.choices(), default="pending"
    )
    notes = models.TextField(blank=True)
    symptoms = models.TextField(blank=True)
    prescription = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "appointments"
        unique_together = ["doctor", "appointment_date", "appointment_time"]
        ordering = ["appointment_date", "appointment_time"]

    def __str__(self):
        return f"{self.patient.user.full_name} - {self.doctor.user.full_name} ({self.appointment_date})"

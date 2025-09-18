from core.models import BaseModel
from django.db import models

from apps.account.models import Doctor, Patient
from core.enum import AppointmentStatus


class Appointment(BaseModel):

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="appointments"
    )
    doctor = models.ForeignKey(
        Doctor, on_delete=models.CASCADE, related_name="appointments"
    )
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(
        max_length=15,
        choices=AppointmentStatus.choices(),
        default=AppointmentStatus.PENDING,
    )
    notes = models.TextField(blank=True)
    symptoms = models.TextField(blank=True)
    prescription = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "appointments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.patient.user.full_name} - {self.doctor.user.full_name}"

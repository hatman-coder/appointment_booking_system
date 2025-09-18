from django.contrib import admin
from .models import Appointment


class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "patient_name",
        "doctor_name",
        "appointment_date",
        "appointment_time",
        "status",
        "created_at",
    )
    list_filter = ("status", "appointment_date", "doctor", "patient")
    search_fields = (
        "patient__user__full_name",
        "doctor__user__full_name",
        "notes",
        "symptoms",
        "prescription",
    )
    ordering = ("-created_at",)
    date_hierarchy = "appointment_date"

    def patient_name(self, obj):
        return obj.patient.user.full_name

    patient_name.short_description = "Patient"

    def doctor_name(self, obj):
        return obj.doctor.user.full_name

    doctor_name.short_description = "Doctor"


admin.site.register(Appointment, AppointmentAdmin)

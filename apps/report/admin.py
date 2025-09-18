from django.contrib import admin
from .models import MonthlyReport, AppointmentReminder


class MonthlyReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "doctor_name",
        "month",
        "year",
        "total_patients",
        "total_appointments",
        "total_earnings",
        "created_at",
    )
    list_filter = ("year", "month", "doctor")
    search_fields = ("doctor__user__full_name",)
    ordering = ("-year", "-month")

    def doctor_name(self, obj):
        return obj.doctor.user.full_name

    doctor_name.short_description = "Doctor"


class AppointmentReminderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "appointment",
        "reminder_sent",
        "sent_at",
        "created_at",
    )
    list_filter = ("reminder_sent", "sent_at")
    search_fields = (
        "appointment__patient__user__full_name",
        "appointment__doctor__user__full_name",
    )
    ordering = ("-created_at",)


admin.site.register(MonthlyReport, MonthlyReportAdmin)
admin.site.register(AppointmentReminder, AppointmentReminderAdmin)

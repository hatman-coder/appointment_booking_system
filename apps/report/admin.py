from django.contrib import admin

from .models import MonthlyReport


@admin.register(MonthlyReport)
class MonthlyReportAdmin(admin.ModelAdmin):
    list_display = [
        "doctor",
        "month",
        "year",
        "total_patients",
        "total_appointments",
        "total_earnings",
    ]
    list_filter = ["year", "month"]
    search_fields = ["doctor__user__full_name"]
    readonly_fields = ["created_at", "updated_at"]


# utils/permissions.py
from rest_framework import permissions


class IsAdminOrDoctorOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.user_type == "admin":
            return True
        elif user.user_type == "doctor":
            return obj.doctor.user == user
        return False

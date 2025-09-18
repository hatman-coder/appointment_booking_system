from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Doctor, DoctorSchedule, Patient


class UserAdmin(BaseUserAdmin):
    list_display = (
        "id",
        "full_name",
        "email",
        "mobile_number",
        "user_type",
        "is_active",
    )
    list_filter = (
        "user_type",
        "is_active",
        "is_staff",
        "is_superuser",
        "division",
        "district",
        "thana",
    )
    search_fields = ("full_name", "email", "mobile_number")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal info",
            {"fields": ("full_name", "username", "mobile_number", "profile_image")},
        ),
        ("Location info", {"fields": ("division", "district", "thana")}),
        ("User type", {"fields": ("user_type",)}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "full_name",
                    "mobile_number",
                    "user_type",
                    "password1",
                    "password2",
                ),
            },
        ),
    )


class DoctorScheduleInline(admin.TabularInline):
    model = DoctorSchedule
    extra = 1


class DoctorAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "license_number",
        "specialization",
        "experience_years",
        "consultation_fee",
        "is_available",
    )
    list_filter = ("specialization", "is_available")
    search_fields = ("user__full_name", "license_number")
    ordering = ("-created_at",)
    inlines = [DoctorScheduleInline]


class PatientAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "date_of_birth", "blood_group", "emergency_contact")
    list_filter = ("blood_group",)
    search_fields = ("user__full_name", "emergency_contact")
    ordering = ("-created_at",)


class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "doctor",
        "day_of_week",
        "start_time",
        "end_time",
        "is_active",
    )
    list_filter = ("day_of_week", "is_active")
    search_fields = ("doctor__user__full_name",)
    ordering = ("doctor", "day_of_week")


admin.site.register(User, UserAdmin)
admin.site.register(Doctor, DoctorAdmin)
admin.site.register(Patient, PatientAdmin)
admin.site.register(DoctorSchedule, DoctorScheduleAdmin)

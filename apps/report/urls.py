from django.urls import path, include
from . import views

app_name = "reports"

# Monthly report URLs
monthly_patterns = [
    # Monthly report generation
    path("monthly/", views.generate_monthly_report, name="own_monthly_report"),
    path(
        "monthly/<int:doctor_id>/",
        views.generate_monthly_report,
        name="doctor_monthly_report",
    ),
    # System monthly reports (Admin only)
    path(
        "system/monthly/", views.get_system_monthly_report, name="system_monthly_report"
    ),
]

# Annual reports URLs
annual_patterns = [
    # Annual summaries
    path("annual/", views.get_doctor_annual_summary, name="own_annual_summary"),
    path(
        "annual/<int:doctor_id>/",
        views.get_doctor_annual_summary,
        name="doctor_annual_summary",
    ),
]

# Analytics and dashboard URLs
analytics_patterns = [
    # Dashboard analytics (role-based)
    path("dashboard/", views.get_dashboard_analytics, name="dashboard_analytics"),
]

# Admin URLs (Admin only endpoints)
admin_patterns = [
    # Bulk operations
    path("bulk-generate/", views.bulk_generate_reports, name="bulk_generate"),
    # System statistics
    path("statistics/", views.get_report_statistics, name="report_statistics"),
]

# Main URL patterns
urlpatterns = [
    # Health check
    path("health/", views.health_check, name="health_check"),
    # Monthly reports
    path("", include((monthly_patterns, "monthly"))),
    # Annual reports
    path("", include((annual_patterns, "annual"))),
    # Analytics and dashboard
    path("", include((analytics_patterns, "analytics"))),
    # Admin operations
    path("admin/", include((admin_patterns, "admin"))),
]

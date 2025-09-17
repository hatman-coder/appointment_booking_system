from django.urls import path, include
from . import views

app_name = "appointments"

# Core appointment operation URLs
appointment_patterns = [
    # Appointment CRUD operations
    path("book/", views.book_appointment, name="book_appointment"),
    path("", views.get_user_appointments, name="user_appointments"),
    path(
        "<int:appointment_id>/", views.get_appointment_detail, name="appointment_detail"
    ),
    path(
        "<int:appointment_id>/status/",
        views.update_appointment_status,
        name="update_status",
    ),
    path(
        "<int:appointment_id>/reschedule/",
        views.reschedule_appointment,
        name="reschedule",
    ),
    path(
        "<int:appointment_id>/cancel/", views.cancel_appointment, name="cancel"
    ),  # Alternative to DELETE
]

# Schedule and availability URLs
schedule_patterns = [
    # Doctor schedule management
    path(
        "schedule/", views.get_doctor_schedule, name="own_schedule"
    ),  # Doctor's own schedule
    path(
        "schedule/<int:doctor_id>/", views.get_doctor_schedule, name="doctor_schedule"
    ),
    path(
        "available-slots/<int:doctor_id>/",
        views.get_available_slots,
        name="available_slots",
    ),
]

# History and analytics URLs
history_patterns = [
    # Patient appointment history
    path(
        "history/", views.get_patient_history, name="own_history"
    ),  # Patient's own history
    path(
        "history/<int:patient_id>/", views.get_patient_history, name="patient_history"
    ),
    path(
        "statistics/", views.get_appointment_statistics, name="appointment_statistics"
    ),
]

# Admin URLs (Admin only endpoints)
admin_patterns = [
    # Advanced admin operations
    path("all/", views.get_all_appointments_admin, name="admin_all_appointments"),
]

# Main URL patterns
urlpatterns = [
    # Core appointment operations
    path("", include((appointment_patterns, "core"))),
    # Schedule and availability
    path("", include((schedule_patterns, "schedule"))),
    # History and analytics
    path("", include((history_patterns, "history"))),
    # Admin operations
    path("admin/", include((admin_patterns, "admin"))),
]

# Alternative: RESTful DELETE endpoint for cancellation
urlpatterns += [
    path(
        "<int:appointment_id>/", views.cancel_appointment, name="delete_appointment"
    ),  # DELETE method
]

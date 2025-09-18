from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = "users"

# Authentication URLs
auth_patterns = [
    # User Authentication
    path("register/", views.register_user, name="register"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    # JWT Token Management
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

# Profile Management URLs
profile_patterns = [
    # Profile Operations
    path("profile/", views.get_user_profile, name="get_profile"),
    path("profile/update/", views.update_user_profile, name="update_profile"),
    path("profile/change-password/", views.change_password, name="change_password"),
    # Dashboard
    path("dashboard/", views.get_dashboard, name="dashboard"),
]

# Doctor-related URLs
doctor_patterns = [
    # Doctors List and Search
    path("doctors/", views.get_doctors_list, name="doctors_list"),
    path("doctors/<uuid:doctor_id>/", views.get_doctor_detail, name="doctor_detail"),
]

# Admin URLs (Admin only endpoints)
admin_patterns = [
    # User Management (Admin only)
    path("users/", views.get_users_list, name="admin_users_list"),
]

# Main URL patterns
urlpatterns = [
    # Authentication routes
    path("auth/", include((auth_patterns, "auth"))),
    # Profile management routes
    path("", include((profile_patterns, "profile"))),
    # Doctor-related routes
    path("", include((doctor_patterns, "doctors"))),
    # Admin routes
    path("admin/", include((admin_patterns, "admin"))),
]

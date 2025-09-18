from django.urls import path, include
from . import views

app_name = "locations"

# Basic location hierarchy URLs
hierarchy_patterns = [
    # Division endpoints
    path("divisions/", views.get_all_divisions, name="divisions"),
    path(
        "divisions/<uuid:division_id>/districts/",
        views.get_districts_by_division,
        name="districts_by_division",
    ),
    path(
        "divisions/<uuid:division_id>/complete/",
        views.get_districts_and_thanas,
        name="complete_division_data",
    ),
    # District endpoints
    path(
        "districts/<uuid:district_id>/thanas/",
        views.get_thanas_by_district,
        name="thanas_by_district",
    ),
    # Hierarchy and validation
    path("hierarchy/", views.get_location_hierarchy, name="location_hierarchy"),
    path("validate/", views.validate_location_hierarchy, name="validate_hierarchy"),
    path("breadcrumb/", views.get_location_breadcrumb, name="location_breadcrumb"),
]

# Search and utility URLs
utility_patterns = [
    # Search functionality
    path("search/", views.search_locations, name="search_locations"),
    # Complete location tree
    path("tree/", views.get_location_tree, name="location_tree"),
    # Statistics (authenticated users)
    path("statistics/", views.get_location_statistics, name="location_statistics"),
]

# Admin URLs (Admin only endpoints)
admin_patterns = [
    # Cache management
    path("clear-cache/", views.clear_location_cache, name="clear_cache"),
]

# Main URL patterns
urlpatterns = [
    # Basic location hierarchy
    path("", include((hierarchy_patterns, "hierarchy"))),
    # Search and utilities
    path("", include((utility_patterns, "utility"))),
    # Admin operations
    path("admin/", include((admin_patterns, "admin"))),
]

from django.urls import path
from . import views

urlpatterns = [
    path("monthly/", views.monthly_reports_list, name="monthly-reports"),
    path("generate/", views.generate_monthly_report, name="generate-report"),
]

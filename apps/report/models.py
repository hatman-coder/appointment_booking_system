from django.db import models
from apps.account.models import Doctor


class MonthlyReport(models.Model):
    doctor = models.ForeignKey(
        Doctor, on_delete=models.CASCADE, related_name="monthly_reports"
    )
    month = models.PositiveIntegerField()  # 1-12
    year = models.PositiveIntegerField()
    total_patients = models.PositiveIntegerField(default=0)
    total_appointments = models.PositiveIntegerField(default=0)
    total_earnings = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "monthly_reports"
        unique_together = ["doctor", "month", "year"]

    def __str__(self):
        return f"{self.doctor.user.full_name} - {self.month}/{self.year}"

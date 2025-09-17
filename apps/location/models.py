from core.models import BaseModel
from django.db import models


class Division(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)

    class Meta:
        db_table = "divisions"
        ordering = ["name"]

    def __str__(self):
        return self.name


class District(BaseModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    division = models.ForeignKey(
        Division, on_delete=models.CASCADE, related_name="districts"
    )

    class Meta:
        db_table = "districts"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Thana(BaseModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    district = models.ForeignKey(
        District, on_delete=models.CASCADE, related_name="thanas"
    )

    class Meta:
        db_table = "thanas"
        ordering = ["name"]

    def __str__(self):
        return self.name

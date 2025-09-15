from core.enum import UserType
from core.models import BaseModel
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import 
from django.core.validators import FileExtensionValidator
from django.db import models
from PIL import Image
from .utils import phone_validator, user_profile_image_path, validate_image_size


from apps.location.models import District, Division, Thana



class User(AbstractUser, BaseModel):

    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    mobile_number = models.CharField(
        max_length=14, validators=[phone_validator()], unique=True
    )
    user_type = models.CharField(max_length=10, choices=UserType.choices())
    division = models.ForeignKey(Division, on_delete=models.SET_NULL, null=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True)
    thana = models.ForeignKey(Thana, on_delete=models.SET_NULL, null=True)
    profile_image = models.ImageField(
        upload_to=user_profile_image_path,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png"]),
            validate_image_size,
        ],
    )
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "full_name", "mobile_number", "user_type"]

    class Meta:
        db_table = "users"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.profile_image:
            img = Image.open(self.profile_image.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.profile_image.path)

    def __str__(self):
        return self.full_name


class Doctor(models.Model):
    SPECIALIZATIONS = [
        ("cardiology", "Cardiology"),
        ("neurology", "Neurology"),
        ("orthopedics", "Orthopedics"),
        ("pediatrics", "Pediatrics"),
        ("dermatology", "Dermatology"),
        ("psychiatry", "Psychiatry"),
        ("general", "General Medicine"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="doctor_profile"
    )
    license_number = models.CharField(max_length=50, unique=True)
    experience_years = models.PositiveIntegerField()
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    specialization = models.CharField(max_length=20, choices=SPECIALIZATIONS)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "doctors"

    def __str__(self):
        return f"Dr. {self.user.full_name}"


class DoctorSchedule(models.Model):
    DAYS_OF_WEEK = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    doctor = models.ForeignKey(
        Doctor, on_delete=models.CASCADE, related_name="schedules"
    )
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "doctor_schedules"
        unique_together = ["doctor", "day_of_week", "start_time"]

    def __str__(self):
        return f"{self.doctor.user.full_name} - {self.get_day_of_week_display()} ({self.start_time}-{self.end_time})"


class Patient(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="patient_profile"
    )
    date_of_birth = models.DateField(null=True, blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    emergency_contact = models.CharField(max_length=14, blank=True)
    medical_history = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patients"

    def __str__(self):
        return self.user.full_name

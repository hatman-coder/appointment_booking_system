from core.models import BaseModel
from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.location.models import District, Division, Thana


class User(AbstractUser, BaseModel):
    USER_TYPE_CHOICES = [
        ("patient", "Patient"),
        ("doctor", "Doctor"),
        ("admin", "Admin"),
    ]

    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    mobile_number = models.CharField(max_length=14, unique=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    division = models.ForeignKey(
        Division, on_delete=models.SET_NULL, null=True, blank=True
    )
    district = models.ForeignKey(
        District, on_delete=models.SET_NULL, null=True, blank=True
    )
    thana = models.ForeignKey(Thana, on_delete=models.SET_NULL, null=True, blank=True)
    profile_image = models.ImageField(
        upload_to="profile_images/", null=True, blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "full_name"]

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.full_name


class Doctor(BaseModel):
    SPECIALIZATION_CHOICES = [
        ("cardiology", "Cardiology"),
        ("neurology", "Neurology"),
        ("orthopedics", "Orthopedics"),
        ("pediatrics", "Pediatrics"),
        ("dermatology", "Dermatology"),
        ("psychiatry", "Psychiatry"),
        ("general", "General Medicine"),
        ("surgery", "Surgery"),
        ("gynecology", "Gynecology"),
        ("ophthalmology", "Ophthalmology"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="doctor_profile"
    )
    license_number = models.CharField(max_length=50, unique=True)
    experience_years = models.PositiveIntegerField()
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    specialization = models.CharField(max_length=20, choices=SPECIALIZATION_CHOICES)
    is_available = models.BooleanField(default=True)

    class Meta:
        db_table = "doctors"

    def __str__(self):
        return f"Dr. {self.user.full_name}"


class DoctorSchedule(BaseModel):
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

    def __str__(self):
        return f"{self.doctor.user.full_name} - {self.get_day_of_week_display()}"


class Patient(BaseModel):
    BLOOD_GROUP_CHOICES = [
        ("A+", "A+"),
        ("A-", "A-"),
        ("B+", "B+"),
        ("B-", "B-"),
        ("AB+", "AB+"),
        ("AB-", "AB-"),
        ("O+", "O+"),
        ("O-", "O-"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="patient_profile"
    )
    date_of_birth = models.DateField(null=True, blank=True)
    blood_group = models.CharField(
        max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True
    )
    emergency_contact = models.CharField(max_length=14, blank=True)
    medical_history = models.TextField(blank=True)

    class Meta:
        db_table = "patients"

    def __str__(self):
        return self.user.full_name

from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from apps.account.models import User, Doctor, Patient, DoctorSchedule
from apps.location.models import Division, District, Thana
import random


class Command(BaseCommand):
    help = "Create sample users for testing"

    def handle(self, *args, **options):
        self.stdout.write("Creating sample users...")

        # Get some locations for assignment
        dhaka_division = Division.objects.get(name="Dhaka")
        dhaka_district = District.objects.get(name="Dhaka")
        thanas = list(Thana.objects.filter(district=dhaka_district)[:5])

        # Create Admin User
        admin_user = User.objects.create(
            username="admin",
            email="admin@hospital.com",
            full_name="System Administrator",
            mobile_number="+8801700000001",
            user_type="admin",
            division=dhaka_division,
            district=dhaka_district,
            thana=random.choice(thanas),
            password=make_password("admin123"),
            is_staff=True,
            is_superuser=True,
        )
        self.stdout.write(f"Created admin: {admin_user.email}")

        # Create Sample Doctors
        specializations = [
            "cardiology",
            "neurology",
            "orthopedics",
            "pediatrics",
            "dermatology",
        ]
        for i in range(5):
            doctor_user = User.objects.create(
                username=f"doctor{i+1}",
                email=f"doctor{i+1}@hospital.com",
                full_name=f"Dr. Mohammad Ali {i+1}",
                mobile_number=f"+88017000000{i+2:02d}",
                user_type="doctor",
                division=dhaka_division,
                district=dhaka_district,
                thana=random.choice(thanas),
                password=make_password("doctor123"),
            )

            doctor = Doctor.objects.create(
                user=doctor_user,
                license_number=f"BMA-{1000+i}",
                experience_years=random.randint(3, 20),
                consultation_fee=random.randint(500, 2000),
                specialization=specializations[i],
            )

            # Create sample schedules
            for day in range(5):  # Monday to Friday
                DoctorSchedule.objects.create(
                    doctor=doctor, day_of_week=day, start_time="09:00", end_time="17:00"
                )

            self.stdout.write(f"Created doctor: {doctor_user.email}")

        # Create Sample Patients
        for i in range(10):
            patient_user = User.objects.create(
                username=f"patient{i+1}",
                email=f"patient{i+1}@gmail.com",
                full_name=f"Patient User {i+1}",
                mobile_number=f"+88018000000{i+1:02d}",
                user_type="patient",
                division=dhaka_division,
                district=dhaka_district,
                thana=random.choice(thanas),
                password=make_password("patient123"),
            )

            Patient.objects.create(
                user=patient_user,
                blood_group=random.choice(
                    ["A+", "B+", "O+", "AB+", "A-", "B-", "O-", "AB-"]
                ),
                emergency_contact=f"+88019000000{i+1:02d}",
            )

            self.stdout.write(f"Created patient: {patient_user.email}")

        self.stdout.write(self.style.SUCCESS("Sample users created successfully!"))
        self.stdout.write("Login credentials:")
        self.stdout.write("Admin: admin@hospital.com / admin123")
        self.stdout.write("Doctors: doctor1@hospital.com / doctor123 (and so on...)")
        self.stdout.write("Patients: patient1@gmail.com / patient123 (and so on...)")

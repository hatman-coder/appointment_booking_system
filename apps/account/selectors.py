import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from django.db.models import Avg, Count, Q, QuerySet

from apps.appointment.models import Appointment

from .models import Doctor, DoctorSchedule, Patient, User


class UserSelector:
    """Selector class for user-related queries"""

    @staticmethod
    def get_user_by_id(user_id: uuid) -> Optional[User]:
        """Get user by ID with location details"""
        try:
            return User.objects.select_related("division", "district", "thana").get(
                id=user_id
            )
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Get user by email"""
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_user_by_mobile(mobile_number: str) -> Optional[User]:
        """Get user by mobile number"""
        try:
            return User.objects.get(mobile_number=mobile_number)
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_users_by_type(user_type: str) -> QuerySet:
        """Get all users by type"""
        return (
            User.objects.filter(user_type=user_type)
            .select_related("division", "district", "thana")
            .order_by("full_name")
        )

    @staticmethod
    def search_users(query: str, user_type: str = None) -> QuerySet:
        """Search users by name, email or mobile"""
        queryset = User.objects.filter(
            Q(full_name__icontains=query)
            | Q(email__icontains=query)
            | Q(mobile_number__icontains=query)
        ).select_related("division", "district", "thana")

        if user_type:
            queryset = queryset.filter(user_type=user_type)

        return queryset.order_by("full_name")

    @staticmethod
    def get_users_by_location(
        division_id: uuid = None, district_id: uuid = None, thana_id: uuid = None
    ) -> QuerySet:
        """Get users by location"""
        queryset = User.objects.select_related("division", "district", "thana")

        if thana_id:
            queryset = queryset.filter(thana_id=thana_id)
        elif district_id:
            queryset = queryset.filter(district_id=district_id)
        elif division_id:
            queryset = queryset.filter(division_id=division_id)

        return queryset.order_by("full_name")

    @staticmethod
    def check_email_exists(email: str, exclude_id: uuid = None) -> bool:
        """Check if email already exists"""
        queryset = User.objects.filter(email=email)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        return queryset.exists()

    @staticmethod
    def check_mobile_exists(mobile_number: str, exclude_id: uuid = None) -> bool:
        """Check if mobile number already exists"""
        queryset = User.objects.filter(mobile_number=mobile_number)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        return queryset.exists()

    @staticmethod
    def get_users_with_pagination(
        page: int = 0, limit: int = 10, filters: dict = None
    ) -> dict:
        """Get paginated list of users with their location details"""

        queryset = User.objects.select_related("division", "district", "thana")

        # Apply filters
        if filters:
            if "user_type" in filters and filters["user_type"]:
                queryset = queryset.filter(user_type=filters["user_type"])
            if "search" in filters and filters["search"]:
                search = filters["search"]
                queryset = queryset.filter(
                    Q(full_name__icontains=search) | Q(email__icontains=search)
                )

        total = queryset.count()
        pages = (total + limit - 1) // limit
        current_page = max(page, 1)
        start = (current_page - 1) * limit
        end = start + limit

        users = queryset.order_by("full_name")[start:end]

        return {
            "total": total,
            "pages": pages,
            "current_page": current_page,
            "users": users,
        }

    @staticmethod
    def get_total_users_count() -> int:
        return User.objects.all().count()


class DoctorSelector:
    """Selector class for doctor-related queries"""

    @staticmethod
    def get_doctor_by_id(doctor_id: uuid) -> Optional[Doctor]:
        """Get doctor by ID with user and location details"""
        try:
            return Doctor.objects.select_related(
                "user__division", "user__district", "user__thana"
            ).get(id=doctor_id)
        except Doctor.DoesNotExist:
            return None

    @staticmethod
    def get_doctor_by_user(user: uuid) -> Optional[Doctor]:
        """Get doctor by user"""
        try:
            return Doctor.objects.get(user=user)
        except Doctor.DoesNotExist:
            return None

    @staticmethod
    def get_all_doctors() -> QuerySet:
        """Get all doctors with user details"""
        return (
            Doctor.objects.select_related(
                "user__division", "user__district", "user__thana"
            )
            .prefetch_related("schedules")
            .order_by("user__full_name")
        )

    @staticmethod
    def get_doctor_available_slots(
        doctor_id: uuid, date: datetime.date = datetime.now(), duration: int = 30
    ) -> List[Dict]:
        """
        Get available time slots for a doctor on a specific date, excluding booked slots
        """
        # Get day of week (0 = Monday, 6 = Sunday)
        day_of_week = date.weekday()

        # Get doctor's schedule for that day
        schedule = DoctorSchedule.objects.filter(
            doctor_id=doctor_id, day_of_week=day_of_week, is_active=True
        ).first()

        if not schedule:
            return []

        # Generate all possible time slots
        all_slots = []
        current_time = schedule.start_time
        end_time = schedule.end_time

        while current_time < end_time:
            slot_end = (
                datetime.combine(datetime.today(), current_time)
                + timedelta(minutes=duration)
            ).time()

            if slot_end <= end_time:
                all_slots.append(
                    {
                        "start": current_time,
                        "end": slot_end,
                        "formatted_start": current_time.strftime("%I:%M %p"),
                        "formatted_end": slot_end.strftime("%I:%M %p"),
                    }
                )

            current_time = slot_end

        # Get booked appointments for the day
        booked_appointments = Appointment.objects.filter(
            doctor_id=doctor_id, appointment_date=date
        ).values_list("appointment_time", flat=True)

        # Filter out booked slots
        available_slots = [
            slot for slot in all_slots if slot["start"] not in booked_appointments
        ]

        return available_slots

    @staticmethod
    def get_doctors_with_pagination(
        page: int = 0, limit: int = 10, filters: dict = None
    ) -> dict:
        """Get paginated list of doctors with their user and location details"""
        queryset = Doctor.objects.select_related(
            "user__division", "user__district", "user__thana"
        ).prefetch_related("schedules")

        # Apply filters
        if filters:
            if "specialization" in filters and filters["specialization"]:
                queryset = queryset.filter(specialization=filters["specialization"])
            if "search" in filters and filters["search"]:
                search = filters["search"]
                queryset = queryset.filter(
                    Q(user__full_name__icontains=search)
                    | Q(specialization__icontains=search)
                    | Q(license_number__icontains=search)
                )

        total = queryset.count()
        pages = (total + limit - 1) // limit
        current_page = max(page, 1)
        start = (current_page - 1) * limit
        end = start + limit

        doctors = queryset.order_by("user__full_name")[start:end]

        return {
            "total": total,
            "pages": pages,
            "current_page": current_page,
            "doctors": doctors,
        }

    @staticmethod
    def get_available_doctors() -> QuerySet:
        """Get all available doctors"""
        return (
            Doctor.objects.filter(is_available=True)
            .select_related("user__division", "user__district", "user__thana")
            .prefetch_related("schedules")
            .order_by("user__full_name")
        )

    @staticmethod
    def get_doctors_by_specialization(specialization: str) -> QuerySet:
        """Get doctors by specialization"""
        return (
            Doctor.objects.filter(specialization=specialization, is_available=True)
            .select_related("user__division", "user__district", "user__thana")
            .prefetch_related("schedules")
            .order_by("user__full_name")
        )

    @staticmethod
    def get_doctors_by_location(
        division_id: uuid = None, district_id: uuid = None, thana_id: uuid = None
    ) -> QuerySet:
        """Get doctors by location"""
        queryset = Doctor.objects.select_related(
            "user__division", "user__district", "user__thana"
        ).prefetch_related("schedules")

        if thana_id:
            queryset = queryset.filter(user__thana_id=thana_id)
        elif district_id:
            queryset = queryset.filter(user__district_id=district_id)
        elif division_id:
            queryset = queryset.filter(user__division_id=division_id)

        return queryset.filter(is_available=True).order_by("user__full_name")

    @staticmethod
    def search_doctors(query: str) -> QuerySet:
        """Search doctors by name, specialization, or license"""
        return (
            Doctor.objects.filter(
                Q(user__full_name__icontains=query)
                | Q(specialization__icontains=query)
                | Q(license_number__icontains=query)
            )
            .select_related("user__division", "user__district", "user__thana")
            .prefetch_related("schedules")
            .order_by("user__full_name")
        )

    @staticmethod
    def filter_doctors(
        specialization: str = None,
        division_id: uuid = None,
        district_id: uuid = None,
        min_experience: int = None,
        max_fee: int = None,
    ) -> QuerySet:
        """Filter doctors with multiple criteria"""
        queryset = (
            Doctor.objects.filter(is_available=True)
            .select_related("user__division", "user__district", "user__thana")
            .prefetch_related("schedules")
        )

        if specialization:
            queryset = queryset.filter(specialization=specialization)

        if division_id:
            queryset = queryset.filter(user__division_id=division_id)

        if district_id:
            queryset = queryset.filter(user__district_id=district_id)

        if min_experience:
            queryset = queryset.filter(experience_years__gte=min_experience)

        if max_fee:
            queryset = queryset.filter(consultation_fee__lte=max_fee)

        return queryset.order_by("consultation_fee")

    @staticmethod
    def get_doctor_schedule(doctor_id: uuid, day_of_week: int = None) -> QuerySet:
        """Get doctor's schedule"""
        queryset = DoctorSchedule.objects.filter(
            doctor_id=doctor_id, is_active=True
        ).order_by("day_of_week", "start_time")

        if day_of_week is not None:
            queryset = queryset.filter(day_of_week=day_of_week)

        return queryset

    @staticmethod
    def get_doctors_with_stats() -> QuerySet:
        """Get doctors with appointment statistics"""
        return (
            Doctor.objects.select_related(
                "user__division", "user__district", "user__thana"
            )
            .annotate(
                total_appointments=Count("appointments"),
                avg_rating=Avg("appointments__rating"),
            )
            .order_by("-total_appointments")
        )

    @staticmethod
    def check_license_exists(license_number: str, exclude_id: uuid = None) -> bool:
        """Check if license number already exists"""
        queryset = Doctor.objects.filter(license_number=license_number)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        return queryset.exists()

    @staticmethod
    def get_doctors_count() -> int:
        return Doctor.objects.all().count()


class PatientSelector:
    """Selector class for patient-related queries"""

    @staticmethod
    def get_patient_by_id(patient_id: uuid) -> Optional[Patient]:
        """Get patient by ID with user details"""
        try:
            return Patient.objects.select_related(
                "user__division", "user__district", "user__thana"
            ).get(id=patient_id)
        except Patient.DoesNotExist:
            return None

    @staticmethod
    def get_patient_by_user(user: uuid) -> Optional[Patient]:
        """Get patient by user"""
        try:
            return Patient.objects.get(user=user)
        except Patient.DoesNotExist:
            return None

    @staticmethod
    def get_all_patients() -> QuerySet:
        """Get all patients with user details"""
        return Patient.objects.select_related(
            "user__division", "user__district", "user__thana"
        ).order_by("user__full_name")

    @staticmethod
    def search_patients(query: str) -> QuerySet:
        """Search patients by name, email, mobile, or blood group"""
        return (
            Patient.objects.filter(
                Q(user__full_name__icontains=query)
                | Q(user__email__icontains=query)
                | Q(user__mobile_number__icontains=query)
                | Q(blood_group__icontains=query)
            )
            .select_related("user__division", "user__district", "user__thana")
            .order_by("user__full_name")
        )

    @staticmethod
    def get_patients_by_blood_group(blood_group: str) -> QuerySet:
        """Get patients by blood group"""
        return (
            Patient.objects.filter(blood_group=blood_group)
            .select_related("user__division", "user__district", "user__thana")
            .order_by("user__full_name")
        )

    @staticmethod
    def get_patients_with_appointment_count() -> QuerySet:
        """Get patients with their appointment count"""
        return (
            Patient.objects.select_related(
                "user__division", "user__district", "user__thana"
            )
            .annotate(total_appointments=Count("appointments"))
            .order_by("-total_appointments")
        )

    @staticmethod
    def get_patients_count() -> int:
        return Patient.objects.all().count()

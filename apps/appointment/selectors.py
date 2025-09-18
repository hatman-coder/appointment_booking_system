from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from django.db.models import Avg, Count, Q, QuerySet
from django.utils import timezone

from apps.account.models import Doctor, Patient, User
from core.enum import AppointmentStatus, UserType

from .models import Appointment


class AppointmentSelector:
    """Selector class for appointment-related queries"""

    @staticmethod
    def get_appointment_by_id(appointment_id: int) -> Optional[Appointment]:
        """Get appointment by ID with related data"""
        try:
            return Appointment.objects.select_related(
                "patient",
                "doctor",
                "patient__user__division",
                "patient__user__district",
                "patient__user__thana",
                "doctor__user__division",
                "doctor__user__district",
                "doctor__user__thana",
            ).get(id=appointment_id)
        except Appointment.DoesNotExist:
            return None

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Get user by ID - used by services for validation"""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_doctor_by_id(doctor_id: int) -> Optional[User]:
        """Get doctor user by ID - used by services for validation"""
        try:
            return Doctor.objects.get(
                id=doctor_id, user__user_type=UserType.DOCTOR.value
            )
        except Doctor.DoesNotExist:
            return None

    @staticmethod
    def get_all_appointments() -> QuerySet:
        """Get all appointments with related data"""
        return Appointment.objects.select_related("patient", "doctor").order_by(
            "-appointment_date", "-appointment_time"
        )

    @staticmethod
    def get_appointments_count() -> int:
        return Appointment.objects.all().count()

    @staticmethod
    def get_appointments_by_patient(patient_id: int) -> QuerySet:
        """Get all appointments for a patient"""
        return (
            Appointment.objects.filter(patient_id=patient_id)
            .select_related("doctor")
            .order_by("-appointment_date", "-appointment_time")
        )

    @staticmethod
    def get_appointments_by_doctor(doctor_id: int) -> QuerySet:
        """Get all appointments for a doctor"""
        return (
            Appointment.objects.filter(doctor_id=doctor_id)
            .select_related("patient")
            .order_by("-appointment_date", "-appointment_time")
        )

    @staticmethod
    def get_appointments_by_status(status: str) -> QuerySet:
        """Get appointments by status"""
        return (
            Appointment.objects.filter(status=status)
            .select_related("patient", "doctor")
            .order_by("-appointment_date", "-appointment_time")
        )

    @staticmethod
    def get_appointments_by_date_range(start_date: date, end_date: date) -> QuerySet:
        """Get appointments within date range"""
        return (
            Appointment.objects.filter(
                appointment_date__gte=start_date, appointment_date__lte=end_date
            )
            .select_related("patient", "doctor")
            .order_by("appointment_date", "appointment_time")
        )

    @staticmethod
    def get_today_appointments() -> QuerySet:
        """Get today's appointments"""
        today = timezone.now().date()
        return (
            Appointment.objects.filter(appointment_date=today)
            .select_related("patient", "doctor")
            .order_by("appointment_time")
        )

    @staticmethod
    def get_upcoming_appointments(days: int = 7) -> QuerySet:
        """Get upcoming appointments within specified days"""
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=days)
        return (
            Appointment.objects.filter(
                appointment_date__gte=start_date,
                appointment_date__lte=end_date,
                status__in=[
                    AppointmentStatus.PENDING.value,
                    AppointmentStatus.CONFIRMED.value,
                ],
            )
            .select_related("patient", "doctor")
            .order_by("appointment_date", "appointment_time")
        )

    @staticmethod
    def get_doctor_appointments_by_date(
        doctor_id: int, appointment_date: date
    ) -> QuerySet:
        """Get doctor's appointments for a specific date"""
        return (
            Appointment.objects.filter(
                doctor_id=doctor_id, appointment_date=appointment_date
            )
            .select_related("patient")
            .order_by("appointment_time")
        )

    @staticmethod
    def get_doctor_appointments_by_datetime(
        doctor_id: int, appointment_datetime: datetime
    ) -> QuerySet:
        """Get doctor's appointments at exact datetime - used by services for conflict checking"""
        appointment_date = appointment_datetime.date()
        appointment_time = appointment_datetime.time()

        return Appointment.objects.filter(
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status__in=[
                AppointmentStatus.PENDING.value,
                AppointmentStatus.CONFIRMED.value,
            ],
        ).select_related("patient")

    @staticmethod
    def get_doctor_appointments_in_range(
        doctor_id: int, start_datetime: datetime, end_datetime: datetime
    ) -> QuerySet:
        """Get doctor's appointments within datetime range - used by services for conflict checking"""
        return Appointment.objects.filter(
            doctor_id=doctor_id,
            appointment_date__gte=start_datetime.date(),
            appointment_date__lte=end_datetime.date(),
            status__in=[
                AppointmentStatus.PENDING.value,
                AppointmentStatus.CONFIRMED.value,
            ],
        ).select_related("patient")

    @staticmethod
    def get_doctor_appointments_in_date_range(
        doctor_id: int, from_date: date, to_date: date
    ) -> QuerySet:
        """Get doctor's appointments within date range - used by services for schedule"""
        return (
            Appointment.objects.filter(
                doctor_id=doctor_id,
                appointment_date__gte=from_date,
                appointment_date__lte=to_date,
            )
            .select_related("patient")
            .order_by("appointment_date", "appointment_time")
        )

    @staticmethod
    def get_patient_appointment_with_doctor_on_date(
        patient_id: int, doctor_id: int, appointment_date: date
    ) -> Optional[Appointment]:
        """Check if patient has appointment with doctor on specific date - used by services"""
        try:
            return Appointment.objects.get(
                patient_id=patient_id,
                doctor_id=doctor_id,
                appointment_date=appointment_date,
                status__in=[
                    AppointmentStatus.PENDING.value,
                    AppointmentStatus.CONFIRMED.value,
                ],
            )
        except Appointment.DoesNotExist:
            return None

    @staticmethod
    def get_patient_appointments_count_on_date(
        patient_id: int, appointment_date: date
    ) -> int:
        """Get count of patient's appointments on specific date - used by services"""
        return Appointment.objects.filter(
            patient_id=patient_id,
            appointment_date=appointment_date,
            status__in=[
                AppointmentStatus.PENDING.value,
                AppointmentStatus.CONFIRMED.value,
            ],
        ).count()

    @staticmethod
    def get_patient_appointments_history(
        patient_id: int, limit: int = None
    ) -> QuerySet:
        """Get patient's appointment history"""
        queryset = (
            Appointment.objects.filter(patient_id=patient_id)
            .select_related("doctor")
            .order_by("-appointment_date", "-appointment_time")
        )

        if limit:
            queryset = queryset[:limit]

        return queryset

    @staticmethod
    def get_patient_appointments(
        patient_id: int, status_filter: str = None
    ) -> QuerySet:
        """Get patient's appointments with optional status filter - used by services"""
        queryset = (
            Appointment.objects.filter(patient_id=patient_id)
            .select_related("doctor")
            .order_by("-appointment_date", "-appointment_time")
        )

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    @staticmethod
    def get_appointments_for_reminders(reminder_time: datetime) -> QuerySet:
        """Get appointments that need reminders - used by services"""
        target_date = reminder_time.date()
        return (
            Appointment.objects.filter(
                appointment_date=target_date,
                status__in=[
                    AppointmentStatus.PENDING.value,
                    AppointmentStatus.CONFIRMED.value,
                ],
            )
            .select_related("patient", "doctor")
            .order_by("appointment_time")
        )

    @staticmethod
    def search_appointments(query: str) -> QuerySet:
        """Search appointments by patient name, doctor name, or notes"""
        return (
            Appointment.objects.filter(
                Q(patient__full_name__icontains=query)
                | Q(doctor__full_name__icontains=query)
                | Q(notes__icontains=query)
            )
            .select_related("patient", "doctor")
            .order_by("-appointment_date", "-appointment_time")
        )

    @staticmethod
    def filter_appointments(
        doctor_id: int = None,
        patient_id: int = None,
        status: str = None,
        start_date: date = None,
        end_date: date = None,
    ) -> QuerySet:
        """Filter appointments with multiple criteria"""
        queryset = Appointment.objects.select_related("patient", "doctor")

        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)

        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

        if status:
            queryset = queryset.filter(status=status)

        if start_date:
            queryset = queryset.filter(appointment_date__gte=start_date)

        if end_date:
            queryset = queryset.filter(appointment_date__lte=end_date)

        return queryset.order_by("-appointment_date", "-appointment_time")

    @staticmethod
    def check_appointment_slot_available(
        doctor_id: int,
        appointment_date: date,
        appointment_time: str,
        exclude_id: int = None,
    ) -> bool:
        """Check if appointment slot is available"""
        queryset = Appointment.objects.filter(
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status__in=[
                AppointmentStatus.PENDING.value,
                AppointmentStatus.CONFIRMED.value,
            ],
        )

        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)

        return not queryset.exists()

    @staticmethod
    def get_appointment_reminders_due() -> QuerySet:
        """Get appointments that need reminders (24 hours before)"""
        tomorrow = timezone.now().date() + timedelta(days=1)
        return Appointment.objects.filter(
            appointment_date=tomorrow,
            status__in=[
                AppointmentStatus.PENDING.value,
                AppointmentStatus.CONFIRMED.value,
            ],
        ).select_related("patient", "doctor")

    @staticmethod
    def get_past_appointments_to_complete() -> QuerySet:
        """Get past appointments that should be marked as completed"""
        yesterday = timezone.now().date() - timedelta(days=1)
        return Appointment.objects.filter(
            appointment_date__lt=yesterday, status=AppointmentStatus.CONFIRMED.value
        )

    @staticmethod
    def get_appointments_statistics() -> Dict[str, Any]:
        """Get appointment statistics"""
        total_appointments = Appointment.objects.count()
        status_counts = Appointment.objects.values("status").annotate(count=Count("id"))

        today = timezone.now().date()
        today_appointments = Appointment.objects.filter(appointment_date=today).count()

        this_month = today.replace(day=1)
        monthly_appointments = Appointment.objects.filter(
            appointment_date__gte=this_month
        ).count()

        return {
            "total_appointments": total_appointments,
            "today_appointments": today_appointments,
            "monthly_appointments": monthly_appointments,
            "status_breakdown": {
                item["status"]: item["count"] for item in status_counts
            },
        }

    # Pagination methods needed by views
    @staticmethod
    def get_patient_appointments_with_pagination(
        patient_id: int, page: int, limit: int, filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get patient appointments with pagination and filters"""
        from django.core.paginator import Paginator

        queryset = AppointmentSelector.filter_appointments(
            patient_id=patient_id,
            status=filters.get("status"),
            start_date=filters.get("date_from"),
            end_date=filters.get("date_to"),
        )

        paginator = Paginator(queryset, limit)
        appointments_page = paginator.get_page(page)

        appointments_data = []
        for appointment in appointments_page:
            appointments_data.append(
                {
                    "id": appointment.id,
                    "doctor_name": appointment.doctor.full_name,
                    "doctor_id": appointment.doctor.id,
                    "appointment_date": appointment.appointment_date,
                    "appointment_time": appointment.appointment_time,
                    "status": appointment.status,
                    "consultation_fee": float(appointment.doctor.consultation_fee),
                    "notes": appointment.notes,
                    "created_at": appointment.created_at,
                }
            )

        return {
            "appointments": appointments_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total_pages": paginator.num_pages,
                "total_count": paginator.count,
                "has_next": appointments_page.has_next(),
                "has_previous": appointments_page.has_previous(),
            },
        }

    @staticmethod
    def get_doctor_appointments_with_pagination(
        doctor_id: int, page: int, limit: int, filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get doctor appointments with pagination and filters"""
        from django.core.paginator import Paginator

        queryset = AppointmentSelector.filter_appointments(
            doctor_id=doctor_id,
            status=filters.get("status"),
            start_date=filters.get("date_from"),
            end_date=filters.get("date_to"),
        )

        paginator = Paginator(queryset, limit)
        appointments_page = paginator.get_page(page)

        appointments_data = []
        for appointment in appointments_page:
            appointments_data.append(
                {
                    "id": appointment.id,
                    "patient_name": appointment.patient.full_name,
                    "patient_id": appointment.patient.id,
                    "patient_mobile": getattr(appointment.patient, "mobile", ""),
                    "appointment_date": appointment.appointment_date,
                    "appointment_time": appointment.appointment_time,
                    "status": appointment.status,
                    "consultation_fee": float(appointment.doctor.consultation_fee),
                    "notes": appointment.notes,
                    "created_at": appointment.created_at,
                }
            )

        return {
            "appointments": appointments_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total_pages": paginator.num_pages,
                "total_count": paginator.count,
                "has_next": appointments_page.has_next(),
                "has_previous": appointments_page.has_previous(),
            },
        }

    @staticmethod
    def get_all_appointments_with_pagination(
        page: int, limit: int, filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get all appointments with pagination and filters (Admin only)"""
        from django.core.paginator import Paginator

        queryset = AppointmentSelector.filter_appointments(
            status=filters.get("status"),
            start_date=filters.get("date_from"),
            end_date=filters.get("date_to"),
        )

        paginator = Paginator(queryset, limit)
        appointments_page = paginator.get_page(page)

        appointments_data = []
        for appointment in appointments_page:
            appointments_data.append(
                {
                    "id": appointment.id,
                    "patient_name": appointment.patient.full_name,
                    "patient_id": appointment.patient.id,
                    "doctor_name": appointment.doctor.full_name,
                    "doctor_id": appointment.doctor.id,
                    "appointment_date": appointment.appointment_date,
                    "appointment_time": appointment.appointment_time,
                    "status": appointment.status,
                    "consultation_fee": float(appointment.doctor.consultation_fee),
                    "notes": appointment.notes,
                    "created_at": appointment.created_at,
                }
            )

        return {
            "appointments": appointments_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total_pages": paginator.num_pages,
                "total_count": paginator.count,
                "has_next": appointments_page.has_next(),
                "has_previous": appointments_page.has_previous(),
            },
        }

    @staticmethod
    def get_doctor_available_slots(
        doctor_id: int, check_date: date
    ) -> Optional[Dict[str, Any]]:
        """Get doctor's available slots for a specific date"""
        try:
            doctor = User.objects.get(id=doctor_id, user_type=UserType.DOCTOR.value)
        except User.DoesNotExist:
            return None

        if not hasattr(doctor, "available_timeslots") or not doctor.available_timeslots:
            return {"available_slots": [], "booked_slots": [], "doctor_timeslots": []}

        # Get booked appointments for the date
        booked_appointments = Appointment.objects.filter(
            doctor_id=doctor_id,
            appointment_date=check_date,
            status__in=[
                AppointmentStatus.PENDING.value,
                AppointmentStatus.CONFIRMED.value,
            ],
        ).values_list("appointment_time", flat=True)

        booked_slots = [time.strftime("%H:%M") for time in booked_appointments]

        # Parse doctor's timeslots and check availability
        available_slots = []
        doctor_timeslots = []

        for timeslot in doctor.available_timeslots:
            try:
                from .services import AppointmentServices

                start_time, end_time = AppointmentServices.parse_timeslot(timeslot)
                slot_time = start_time.strftime("%H:%M")
                doctor_timeslots.append(slot_time)

                if slot_time not in booked_slots:
                    available_slots.append(slot_time)
            except:
                continue

        return {
            "available_slots": available_slots,
            "booked_slots": booked_slots,
            "doctor_timeslots": doctor_timeslots,
        }

    # Statistics methods for different user types
    @staticmethod
    def get_patient_appointment_statistics(patient_id: int) -> Dict[str, Any]:
        """Get appointment statistics for a specific patient"""
        appointments = Appointment.objects.filter(patient_id=patient_id)

        total = appointments.count()
        completed = appointments.filter(
            status=AppointmentStatus.COMPLETED.value
        ).count()
        pending = appointments.filter(status=AppointmentStatus.PENDING.value).count()
        confirmed = appointments.filter(
            status=AppointmentStatus.CONFIRMED.value
        ).count()
        cancelled = appointments.filter(
            status=AppointmentStatus.CANCELLED.value
        ).count()

        # Upcoming appointments
        today = timezone.now().date()
        upcoming = appointments.filter(
            appointment_date__gte=today,
            status__in=[
                AppointmentStatus.PENDING.value,
                AppointmentStatus.CONFIRMED.value,
            ],
        ).count()

        # Total spent
        total_spent = (
            appointments.filter(status=AppointmentStatus.COMPLETED.value).aggregate(
                total=Count("doctor__consultation_fee")
            )["total"]
            or 0
        )

        return {
            "total_appointments": total,
            "completed_appointments": completed,
            "pending_appointments": pending,
            "confirmed_appointments": confirmed,
            "cancelled_appointments": cancelled,
            "upcoming_appointments": upcoming,
            "total_spent": total_spent,
        }

    @staticmethod
    def get_doctor_appointment_statistics(doctor_id: int) -> Dict[str, Any]:
        """Get appointment statistics for a specific doctor"""
        appointments = Appointment.objects.filter(doctor_id=doctor_id)

        total = appointments.count()
        completed = appointments.filter(
            status=AppointmentStatus.COMPLETED.value
        ).count()
        pending = appointments.filter(status=AppointmentStatus.PENDING.value).count()
        confirmed = appointments.filter(
            status=AppointmentStatus.CONFIRMED.value
        ).count()
        cancelled = appointments.filter(
            status=AppointmentStatus.CANCELLED.value
        ).count()

        # Today's appointments
        today = timezone.now().date()
        today_appointments = appointments.filter(appointment_date=today).count()

        # This month's appointments
        this_month = today.replace(day=1)
        monthly_appointments = appointments.filter(
            appointment_date__gte=this_month
        ).count()

        # Revenue (from completed appointments)
        total_revenue = (
            appointments.filter(status=AppointmentStatus.COMPLETED.value).aggregate(
                revenue=Count("doctor__consultation_fee")
            )["revenue"]
            or 0
        )

        return {
            "total_appointments": total,
            "completed_appointments": completed,
            "pending_appointments": pending,
            "confirmed_appointments": confirmed,
            "cancelled_appointments": cancelled,
            "today_appointments": today_appointments,
            "monthly_appointments": monthly_appointments,
            "total_revenue": total_revenue,
        }

    @staticmethod
    def get_admin_appointment_statistics() -> Dict[str, Any]:
        """Get system-wide appointment statistics for admin"""
        appointments = Appointment.objects.all()

        total = appointments.count()
        completed = appointments.filter(
            status=AppointmentStatus.COMPLETED.value
        ).count()
        pending = appointments.filter(status=AppointmentStatus.PENDING.value).count()
        confirmed = appointments.filter(
            status=AppointmentStatus.CONFIRMED.value
        ).count()
        cancelled = appointments.filter(
            status=AppointmentStatus.CANCELLED.value
        ).count()

        # Today's appointments
        today = timezone.now().date()
        today_appointments = appointments.filter(appointment_date=today).count()

        # This month's appointments
        this_month = today.replace(day=1)
        monthly_appointments = appointments.filter(
            appointment_date__gte=this_month
        ).count()

        # Active doctors and patients
        active_doctors = appointments.values("doctor_id").distinct().count()
        active_patients = appointments.values("patient_id").distinct().count()

        return {
            "total_appointments": total,
            "completed_appointments": completed,
            "pending_appointments": pending,
            "confirmed_appointments": confirmed,
            "cancelled_appointments": cancelled,
            "today_appointments": today_appointments,
            "monthly_appointments": monthly_appointments,
            "active_doctors": active_doctors,
            "active_patients": active_patients,
        }

    @staticmethod
    def get_admin_appointments_with_filters(
        page: int, limit: int, filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get appointments with advanced filtering for admin"""
        from django.core.paginator import Paginator

        queryset = Appointment.objects.select_related("patient", "doctor").all()

        # Apply filters
        if filters.get("status"):
            queryset = queryset.filter(status=filters["status"])
        if filters.get("doctor_id"):
            queryset = queryset.filter(doctor_id=int(filters["doctor_id"]))
        if filters.get("patient_id"):
            queryset = queryset.filter(patient_id=int(filters["patient_id"]))
        if filters.get("date_from"):
            from_date = datetime.strptime(filters["date_from"], "%Y-%m-%d").date()
            queryset = queryset.filter(appointment_date__gte=from_date)
        if filters.get("date_to"):
            to_date = datetime.strptime(filters["date_to"], "%Y-%m-%d").date()
            queryset = queryset.filter(appointment_date__lte=to_date)
        if filters.get("search"):
            search_term = filters["search"]
            queryset = queryset.filter(
                Q(patient__full_name__icontains=search_term)
                | Q(doctor__full_name__icontains=search_term)
                | Q(notes__icontains=search_term)
            )

        queryset = queryset.order_by("-appointment_date", "-appointment_time")

        paginator = Paginator(queryset, limit)
        appointments_page = paginator.get_page(page)

        appointments_data = []
        for appointment in appointments_page:
            appointments_data.append(
                {
                    "id": appointment.id,
                    "patient_name": appointment.patient.user.full_name,
                    "patient_id": appointment.patient.id,
                    "patient_email": appointment.patient.user.email,
                    "doctor_name": appointment.doctor.user.full_name,
                    "doctor_id": appointment.doctor.id,
                    "appointment_date": appointment.appointment_date,
                    "appointment_time": appointment.appointment_time,
                    "status": appointment.status,
                    "consultation_fee": float(appointment.doctor.consultation_fee),
                    "notes": appointment.notes,
                    "created_at": appointment.created_at,
                    "updated_at": appointment.updated_at,
                }
            )

        return {
            "appointments": appointments_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total_pages": paginator.num_pages,
                "total_count": paginator.count,
                "has_next": appointments_page.has_next(),
                "has_previous": appointments_page.has_previous(),
            },
            "filters_applied": filters,
        }

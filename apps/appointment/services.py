import logging
from datetime import datetime, time, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from account.models import User
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import Appointment
from .selectors import AppointmentSelector

logger = logging.getLogger(__name__)


class AppointmentValidationError(Exception):
    """Custom exception for appointment validation errors"""

    pass


class AppointmentServices:
    """Service class for appointment-related business operations"""

    # Business hours configuration
    BUSINESS_START_TIME = time(8, 0)  # 8:00 AM
    BUSINESS_END_TIME = time(20, 0)  # 8:00 PM
    APPOINTMENT_DURATION = 60  # minutes
    MIN_ADVANCE_BOOKING = 60  # minutes (1 hour advance booking required)
    MAX_ADVANCE_BOOKING = 90  # days (3 months max advance booking)

    @staticmethod
    def parse_timeslot(timeslot: str) -> Tuple[time, time]:
        """
        Parse timeslot string to start and end time objects
        Example: "10:00-11:00" -> (time(10, 0), time(11, 0))
        """
        try:
            start_str, end_str = timeslot.split("-")
            start_hour, start_min = map(int, start_str.split(":"))
            end_hour, end_min = map(int, end_str.split(":"))
            return time(start_hour, start_min), time(end_hour, end_min)
        except (ValueError, AttributeError):
            raise AppointmentValidationError(f"Invalid timeslot format: {timeslot}")

    @staticmethod
    def is_within_business_hours(appointment_time: datetime) -> bool:
        """
        Check if appointment time is within business hours
        """
        appointment_time_only = appointment_time.time()
        return (
            AppointmentServices.BUSINESS_START_TIME
            <= appointment_time_only
            <= AppointmentServices.BUSINESS_END_TIME
        )

    @staticmethod
    def validate_appointment_time(appointment_datetime: datetime) -> Tuple[bool, str]:
        """
        Validate appointment date and time
        """
        now = timezone.now()

        # Check if appointment is in the past
        if appointment_datetime <= now:
            return False, "Appointment time cannot be in the past"

        # Check minimum advance booking time
        min_time = now + timedelta(minutes=AppointmentServices.MIN_ADVANCE_BOOKING)
        if appointment_datetime < min_time:
            return (
                False,
                f"Appointment must be booked at least {AppointmentServices.MIN_ADVANCE_BOOKING} minutes in advance",
            )

        # Check maximum advance booking time
        max_time = now + timedelta(days=AppointmentServices.MAX_ADVANCE_BOOKING)
        if appointment_datetime > max_time:
            return (
                False,
                f"Appointment cannot be booked more than {AppointmentServices.MAX_ADVANCE_BOOKING} days in advance",
            )

        # Check if within business hours
        if not AppointmentServices.is_within_business_hours(appointment_datetime):
            return (
                False,
                f"Appointment must be between {AppointmentServices.BUSINESS_START_TIME} and {AppointmentServices.BUSINESS_END_TIME}",
            )

        # Check if it's not a weekend (optional - can be configured)
        if appointment_datetime.weekday() == 6:  # Sunday = 6
            return False, "Appointments are not available on Sundays"

        return True, ""

    @staticmethod
    def check_doctor_availability(
        doctor_id: int, appointment_datetime: datetime
    ) -> Tuple[bool, str]:
        """
        Check if doctor is available at the requested time
        """
        doctor = AppointmentSelector.get_doctor_by_id(doctor_id)
        if not doctor:
            return False, "Doctor not found"

        # Check doctor's available timeslots
        appointment_time = appointment_datetime.time()
        appointment_weekday = appointment_datetime.weekday()

        # Check if the appointment time falls within any of the doctor's available timeslots
        if not hasattr(doctor, "available_timeslots") or not doctor.available_timeslots:
            return False, "Doctor has no available timeslots"

        time_slot_available = False
        for timeslot in doctor.available_timeslots:
            try:
                start_time, end_time = AppointmentServices.parse_timeslot(timeslot)
                if start_time <= appointment_time < end_time:
                    time_slot_available = True
                    break
            except AppointmentValidationError:
                continue

        if not time_slot_available:
            return (
                False,
                f"Doctor is not available at {appointment_time.strftime('%H:%M')}",
            )

        # Check for existing appointments at the same time
        existing_appointments = AppointmentSelector.get_doctor_appointments_by_datetime(
            doctor_id, appointment_datetime
        )

        if existing_appointments.exists():
            return False, "Doctor already has an appointment at this time"

        # Check for conflicting appointments (within appointment duration)
        start_conflict_time = appointment_datetime - timedelta(
            minutes=AppointmentServices.APPOINTMENT_DURATION
        )
        end_conflict_time = appointment_datetime + timedelta(
            minutes=AppointmentServices.APPOINTMENT_DURATION
        )

        conflicting_appointments = AppointmentSelector.get_doctor_appointments_in_range(
            doctor_id, start_conflict_time, end_conflict_time
        )

        if conflicting_appointments.exists():
            return False, "Doctor has a conflicting appointment within the time range"

        return True, ""

    @staticmethod
    def calculate_appointment_fee(doctor_id: int) -> Optional[Decimal]:
        """
        Calculate appointment fee based on doctor's consultation fee
        """
        doctor = AppointmentSelector.get_doctor_by_id(doctor_id)
        if not doctor:
            return None

        # Assuming consultation_fee is an attribute of the doctor
        if hasattr(doctor, "consultation_fee"):
            return Decimal(str(doctor.consultation_fee))
        else:
            # Default fee if not set
            return Decimal("500.00")

    @classmethod
    def book_appointment(cls, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Book a new appointment with comprehensive validation
        """
        try:
            with transaction.atomic():
                # Extract required data
                patient_id = appointment_data.get("patient_id")
                doctor_id = appointment_data.get("doctor_id")
                appointment_date = appointment_data.get("appointment_date")
                appointment_time = appointment_data.get("appointment_time")
                notes = appointment_data.get("notes", "").strip()

                # Basic validation
                if not all([patient_id, doctor_id, appointment_date, appointment_time]):
                    raise AppointmentValidationError(
                        "Patient ID, Doctor ID, appointment date, and time are required"
                    )

                # Validate patient exists and is a patient
                patient = AppointmentSelector.get_user_by_id(patient_id)
                if not patient:
                    raise AppointmentValidationError("Patient not found")

                if patient.user_type != UserType.PATIENT.value:
                    raise AppointmentValidationError(
                        "Only patients can book appointments"
                    )

                # Validate doctor exists and is a doctor
                doctor = AppointmentSelector.get_doctor_by_id(doctor_id)
                if not doctor:
                    raise AppointmentValidationError("Doctor not found")

                # Parse and validate appointment datetime
                try:
                    if isinstance(appointment_date, str):
                        appointment_date = datetime.strptime(
                            appointment_date, "%Y-%m-%d"
                        ).date()

                    if isinstance(appointment_time, str):
                        appointment_time = datetime.strptime(
                            appointment_time, "%H:%M"
                        ).time()

                    appointment_datetime = timezone.make_aware(
                        datetime.combine(appointment_date, appointment_time)
                    )
                except (ValueError, TypeError) as e:
                    raise AppointmentValidationError(
                        f"Invalid date/time format: {str(e)}"
                    )

                # Validate appointment time
                is_valid_time, time_error = cls.validate_appointment_time(
                    appointment_datetime
                )
                if not is_valid_time:
                    raise AppointmentValidationError(time_error)

                # Check doctor availability
                is_available, availability_error = cls.check_doctor_availability(
                    doctor_id, appointment_datetime
                )
                if not is_available:
                    raise AppointmentValidationError(availability_error)

                # Check if patient already has an appointment with the same doctor on the same day
                existing_appointment = (
                    AppointmentSelector.get_patient_appointment_with_doctor_on_date(
                        patient_id, doctor_id, appointment_date
                    )
                )
                if existing_appointment:
                    raise AppointmentValidationError(
                        "You already have an appointment with this doctor on this date"
                    )

                # Check patient's appointment limit per day (e.g., max 3 appointments per day)
                patient_appointments_count = (
                    AppointmentSelector.get_patient_appointments_count_on_date(
                        patient_id, appointment_date
                    )
                )
                if patient_appointments_count >= 3:
                    raise AppointmentValidationError(
                        "Maximum 3 appointments allowed per day"
                    )

                # Calculate fee
                consultation_fee = cls.calculate_appointment_fee(doctor_id)
                if consultation_fee is None:
                    raise AppointmentValidationError(
                        "Unable to calculate appointment fee"
                    )

                # Create appointment
                appointment = Appointment.objects.create(
                    patient=patient,
                    doctor=doctor,
                    appointment_date=appointment_date,
                    appointment_time=appointment_time,
                    notes=notes,
                    status=Appointment.PENDING,
                    consultation_fee=consultation_fee,
                )

                logger.info(
                    f"Appointment booked successfully: ID {appointment.id}, Patient: {patient.email}, Doctor: {doctor.email}"
                )

                return {
                    "success": True,
                    "message": "Appointment booked successfully",
                    "appointment_id": appointment.id,
                    "appointment_details": {
                        "id": appointment.id,
                        "appointment_date": appointment.appointment_date,
                        "appointment_time": appointment.appointment_time,
                        "doctor_name": doctor.full_name,
                        "consultation_fee": float(consultation_fee),
                        "status": appointment.status,
                    },
                }

        except AppointmentValidationError as e:
            logger.warning(f"Appointment booking validation error: {str(e)}")
            return {"success": False, "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error during appointment booking: {str(e)}")
            return {
                "success": False,
                "message": "Appointment booking failed due to server error",
            }

    @staticmethod
    def update_appointment_status(
        appointment_id: int, new_status: str, updated_by_user_id: int
    ) -> Dict[str, Any]:
        """
        Update appointment status with proper authorization
        """
        try:
            with transaction.atomic():
                appointment = AppointmentSelector.get_appointment_by_id(appointment_id)
                if not appointment:
                    return {"success": False, "message": "Appointment not found"}

                # Get the user making the update
                updater = AppointmentSelector.get_user_by_id(updated_by_user_id)
                if not updater:
                    return {"success": False, "message": "User not found"}

                # Validate new status
                if new_status not in [
                    choice[0] for choice in Appointment.STATUS_CHOICES
                ]:
                    return {"success": False, "message": "Invalid appointment status"}

                # Authorization checks
                can_update = False

                if updater.user_type == UserType.ADMIN.value:
                    # Admin can update any appointment
                    can_update = True
                elif (
                    updater.user_type == UserType.DOCTOR.value
                    and updater.id == appointment.doctor.id
                ):
                    # Doctor can update their own appointments
                    can_update = True
                elif (
                    updater.user_type == UserType.PATIENT.value
                    and updater.id == appointment.patient.id
                ):
                    # Patient can only cancel their own appointments
                    if new_status == Appointment.CANCELLED:
                        can_update = True
                    else:
                        return {
                            "success": False,
                            "message": "Patients can only cancel their appointments",
                        }

                if not can_update:
                    return {
                        "success": False,
                        "message": "Insufficient permissions to update this appointment",
                    }

                # Status transition validation
                current_status = appointment.status

                # Define valid status transitions
                valid_transitions = {
                    Appointment.PENDING: [Appointment.CONFIRMED, Appointment.CANCELLED],
                    Appointment.CONFIRMED: [
                        Appointment.COMPLETED,
                        Appointment.CANCELLED,
                    ],
                    Appointment.CANCELLED: [],  # Cannot change from cancelled
                    Appointment.COMPLETED: [],  # Cannot change from completed
                }

                if new_status not in valid_transitions.get(current_status, []):
                    return {
                        "success": False,
                        "message": f"Cannot change appointment status from {current_status} to {new_status}",
                    }

                # Additional validations for specific status changes
                if new_status == Appointment.COMPLETED:
                    # Can only complete appointments that are in the past or current
                    appointment_datetime = timezone.make_aware(
                        datetime.combine(
                            appointment.appointment_date, appointment.appointment_time
                        )
                    )
                    if appointment_datetime > timezone.now():
                        return {
                            "success": False,
                            "message": "Cannot complete future appointments",
                        }

                # Update appointment status
                old_status = appointment.status
                appointment.status = new_status
                appointment.updated_at = timezone.now()
                appointment.save(update_fields=["status", "updated_at"])

                logger.info(
                    f"Appointment status updated: ID {appointment.id}, {old_status} -> {new_status}, by {updater.email}"
                )

                return {
                    "success": True,
                    "message": f"Appointment status updated to {new_status}",
                    "appointment_id": appointment.id,
                    "old_status": old_status,
                    "new_status": new_status,
                }

        except Exception as e:
            logger.error(f"Error updating appointment status: {str(e)}")
            return {"success": False, "message": "Failed to update appointment status"}

    @classmethod
    def reschedule_appointment(
        cls, appointment_id: int, new_date: str, new_time: str, user_id: int
    ) -> Dict[str, Any]:
        """
        Reschedule an existing appointment
        """
        try:
            with transaction.atomic():
                appointment = AppointmentSelector.get_appointment_by_id(appointment_id)
                if not appointment:
                    return {"success": False, "message": "Appointment not found"}

                # Authorization check
                user = AppointmentSelector.get_user_by_id(user_id)
                if not user:
                    return {"success": False, "message": "User not found"}

                can_reschedule = (
                    user.user_type == UserType.ADMIN.value
                    or (
                        user.user_type == UserType.PATIENT.value
                        and user.id == appointment.patient.id
                    )
                    or (
                        user.user_type == UserType.DOCTOR.value
                        and user.id == appointment.doctor.id
                    )
                )

                if not can_reschedule:
                    return {
                        "success": False,
                        "message": "Insufficient permissions to reschedule this appointment",
                    }

                # Can only reschedule pending or confirmed appointments
                if appointment.status not in [
                    Appointment.PENDING,
                    Appointment.CONFIRMED,
                ]:
                    return {
                        "success": False,
                        "message": "Can only reschedule pending or confirmed appointments",
                    }

                # Parse new date and time
                try:
                    new_appointment_date = datetime.strptime(
                        new_date, "%Y-%m-%d"
                    ).date()
                    new_appointment_time = datetime.strptime(new_time, "%H:%M").time()
                    new_appointment_datetime = timezone.make_aware(
                        datetime.combine(new_appointment_date, new_appointment_time)
                    )
                except (ValueError, TypeError) as e:
                    return {
                        "success": False,
                        "message": f"Invalid date/time format: {str(e)}",
                    }

                # Validate new appointment time
                is_valid_time, time_error = cls.validate_appointment_time(
                    new_appointment_datetime
                )
                if not is_valid_time:
                    return {"success": False, "message": time_error}

                # Check doctor availability for new time
                is_available, availability_error = cls.check_doctor_availability(
                    appointment.doctor.id, new_appointment_datetime
                )
                if not is_available:
                    return {"success": False, "message": availability_error}

                # Update appointment
                old_date = appointment.appointment_date
                old_time = appointment.appointment_time

                appointment.appointment_date = new_appointment_date
                appointment.appointment_time = new_appointment_time
                appointment.status = (
                    Appointment.CONFIRMED
                )  # Rescheduled appointments are confirmed
                appointment.updated_at = timezone.now()
                appointment.save(
                    update_fields=[
                        "appointment_date",
                        "appointment_time",
                        "status",
                        "updated_at",
                    ]
                )

                logger.info(
                    f"Appointment rescheduled: ID {appointment.id}, {old_date} {old_time} -> {new_appointment_date} {new_appointment_time}"
                )

                return {
                    "success": True,
                    "message": "Appointment rescheduled successfully",
                    "appointment_id": appointment.id,
                    "old_datetime": f"{old_date} {old_time}",
                    "new_datetime": f"{new_appointment_date} {new_appointment_time}",
                }

        except Exception as e:
            logger.error(f"Error rescheduling appointment: {str(e)}")
            return {"success": False, "message": "Failed to reschedule appointment"}

    @staticmethod
    def cancel_appointment(
        appointment_id: int, user_id: int, cancellation_reason: str = ""
    ) -> Dict[str, Any]:
        """
        Cancel an appointment
        """
        try:
            cancellation_result = AppointmentServices.update_appointment_status(
                appointment_id, Appointment.CANCELLED, user_id
            )

            if cancellation_result["success"]:
                # Add cancellation reason if provided
                if cancellation_reason:
                    appointment = AppointmentSelector.get_appointment_by_id(
                        appointment_id
                    )
                    if appointment:
                        # Add to notes or create a separate cancellation_reason field
                        current_notes = appointment.notes or ""
                        appointment.notes = f"{current_notes}\nCancellation reason: {cancellation_reason}".strip()
                        appointment.save(update_fields=["notes"])

                logger.info(
                    f"Appointment cancelled: ID {appointment_id}, Reason: {cancellation_reason}"
                )

                return {
                    "success": True,
                    "message": "Appointment cancelled successfully",
                    "appointment_id": appointment_id,
                }
            else:
                return cancellation_result

        except Exception as e:
            logger.error(f"Error cancelling appointment: {str(e)}")
            return {"success": False, "message": "Failed to cancel appointment"}

    @staticmethod
    def get_appointment_reminders(hours_ahead: int = 24) -> List[Dict[str, Any]]:
        """
        Get appointments that need reminders (for scheduler task)
        """
        try:
            reminder_time = timezone.now() + timedelta(hours=hours_ahead)
            appointments = AppointmentSelector.get_appointments_for_reminders(
                reminder_time
            )

            reminders = []
            for appointment in appointments:
                appointment_datetime = timezone.make_aware(
                    datetime.combine(
                        appointment.appointment_date, appointment.appointment_time
                    )
                )

                reminders.append(
                    {
                        "appointment_id": appointment.id,
                        "patient_email": appointment.patient.email,
                        "patient_name": appointment.patient.full_name,
                        "patient_mobile": getattr(appointment.patient, "mobile", ""),
                        "doctor_name": appointment.doctor.full_name,
                        "appointment_datetime": appointment_datetime,
                        "consultation_fee": float(appointment.consultation_fee),
                        "notes": appointment.notes,
                    }
                )

            logger.info(f"Found {len(reminders)} appointments for reminders")
            return reminders

        except Exception as e:
            logger.error(f"Error getting appointment reminders: {str(e)}")
            return []

    @staticmethod
    def get_doctor_schedule(
        doctor_id: int, date_from: str, date_to: str
    ) -> Dict[str, Any]:
        """
        Get doctor's schedule for a date range
        """
        try:
            doctor = AppointmentSelector.get_doctor_by_id(doctor_id)
            if not doctor:
                return {"success": False, "message": "Doctor not found"}

            # Parse dates
            try:
                from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
                to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
            except ValueError:
                return {
                    "success": False,
                    "message": "Invalid date format. Use YYYY-MM-DD",
                }

            # Get appointments in the date range
            appointments = AppointmentSelector.get_doctor_appointments_in_date_range(
                doctor_id, from_date, to_date
            )

            # Group appointments by date
            schedule = {}
            current_date = from_date

            while current_date <= to_date:
                date_str = current_date.strftime("%Y-%m-%d")
                day_appointments = [
                    {
                        "id": apt.id,
                        "time": apt.appointment_time.strftime("%H:%M"),
                        "patient_name": apt.patient.full_name,
                        "patient_mobile": getattr(apt.patient, "mobile", ""),
                        "status": apt.status,
                        "notes": apt.notes,
                        "consultation_fee": float(apt.consultation_fee),
                    }
                    for apt in appointments
                    if apt.appointment_date == current_date
                ]

                # Add available slots
                available_slots = []
                if (
                    hasattr(doctor, "available_timeslots")
                    and doctor.available_timeslots
                ):
                    for timeslot in doctor.available_timeslots:
                        try:
                            start_time, end_time = AppointmentServices.parse_timeslot(
                                timeslot
                            )
                            # Check if this slot is occupied
                            slot_occupied = any(
                                apt["time"] == start_time.strftime("%H:%M")
                                for apt in day_appointments
                            )
                            if not slot_occupied:
                                available_slots.append(timeslot)
                        except AppointmentValidationError:
                            continue

                schedule[date_str] = {
                    "date": date_str,
                    "appointments": day_appointments,
                    "available_slots": available_slots,
                    "total_appointments": len(day_appointments),
                }

                current_date += timedelta(days=1)

            return {
                "success": True,
                "doctor_name": doctor.full_name,
                "schedule": schedule,
            }

        except Exception as e:
            logger.error(f"Error getting doctor schedule: {str(e)}")
            return {"success": False, "message": "Failed to retrieve doctor schedule"}

    @staticmethod
    def get_patient_appointment_history(
        patient_id: int, status_filter: str = None
    ) -> Dict[str, Any]:
        """
        Get patient's appointment history with optional status filter
        """
        try:
            patient = AppointmentSelector.get_user_by_id(patient_id)
            if not patient or patient.user_type != UserType.PATIENT.value:
                return {"success": False, "message": "Patient not found"}

            # Get appointments
            appointments = AppointmentSelector.get_patient_appointments(
                patient_id, status_filter
            )

            # Format appointment data
            appointment_history = []
            for appointment in appointments:
                appointment_datetime = timezone.make_aware(
                    datetime.combine(
                        appointment.appointment_date, appointment.appointment_time
                    )
                )

                appointment_history.append(
                    {
                        "id": appointment.id,
                        "doctor_name": appointment.doctor.full_name,
                        "doctor_license": getattr(
                            appointment.doctor, "license_number", ""
                        ),
                        "appointment_date": appointment.appointment_date,
                        "appointment_time": appointment.appointment_time,
                        "appointment_datetime": appointment_datetime,
                        "status": appointment.status,
                        "consultation_fee": float(appointment.consultation_fee),
                        "notes": appointment.notes,
                        "created_at": appointment.created_at,
                        "updated_at": appointment.updated_at,
                    }
                )

            # Calculate statistics
            stats = {
                "total_appointments": len(appointment_history),
                "completed_appointments": len(
                    [
                        a
                        for a in appointment_history
                        if a["status"] == Appointment.COMPLETED
                    ]
                ),
                "pending_appointments": len(
                    [
                        a
                        for a in appointment_history
                        if a["status"] == Appointment.PENDING
                    ]
                ),
                "cancelled_appointments": len(
                    [
                        a
                        for a in appointment_history
                        if a["status"] == Appointment.CANCELLED
                    ]
                ),
                "total_spent": sum(
                    a["consultation_fee"]
                    for a in appointment_history
                    if a["status"] == Appointment.COMPLETED
                ),
            }

            return {
                "success": True,
                "patient_name": patient.full_name,
                "appointments": appointment_history,
                "statistics": stats,
            }

        except Exception as e:
            logger.error(f"Error getting patient appointment history: {str(e)}")
            return {
                "success": False,
                "message": "Failed to retrieve appointment history",
            }

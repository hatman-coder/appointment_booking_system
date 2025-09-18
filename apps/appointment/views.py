import logging
from datetime import date, datetime, timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Appointment
from .selectors import AppointmentSelector
from .services import AppointmentServices
from core.enum import UserType

logger = logging.getLogger(__name__)


def standardize_response(success: bool, message: str, data=None, status_code=None):
    """
    Standardize API response format
    """
    response_data = {"success": success, "message": message}

    if data is not None:
        if isinstance(data, dict):
            response_data.update(data)
        else:
            response_data["data"] = data

    if status_code is None:
        status_code = status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST

    return Response(response_data, status=status_code)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def book_appointment(request):
    """
    Book a new appointment
    POST /api/appointments/book/

    Expected payload:
    {
        "doctor_id": 1,
        "appointment_date": "2024-03-15",
        "appointment_time": "10:00",
        "notes": "Having fever and headache"
    }
    """
    try:
        # Only patients can book appointments
        if request.user.user_type != UserType.PATIENT.value:
            return standardize_response(
                False,
                "Only patients can book appointments",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # Prepare appointment data
        appointment_data = {
            "patient_id": request.user.id,
            "doctor_id": request.data.get("doctor_id"),
            "appointment_date": request.data.get("appointment_date"),
            "appointment_time": request.data.get("appointment_time"),
            "notes": request.data.get("notes", "").strip(),
        }

        # Validate required fields
        if not all(
            [
                appointment_data["doctor_id"],
                appointment_data["appointment_date"],
                appointment_data["appointment_time"],
            ]
        ):
            return standardize_response(
                False,
                "Doctor ID, appointment date, and time are required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Book appointment
        result = AppointmentServices.book_appointment(appointment_data)

        if result["success"]:
            logger.info(
                f"Appointment booked via API: Patient {request.user.email}, Appointment ID {result['appointment_id']}"
            )
            return standardize_response(
                True,
                result["message"],
                {
                    "appointment_id": result["appointment_id"],
                    "appointment_details": result["appointment_details"],
                },
                status_code=status.HTTP_201_CREATED,
            )
        else:
            return standardize_response(
                False, result["message"], status_code=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        logger.error(f"Book appointment API error: {str(e)}")
        return standardize_response(
            False,
            "Appointment booking failed due to server error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_appointments(request):
    """
    Get user's appointments (patient or doctor specific)
    GET /api/appointments/

    Query parameters:
    - page: Page number (default: 1)
    - limit: Items per page (default: 10)
    - status: Filter by status (pending, confirmed, completed, cancelled)
    - date_from: Filter from date (YYYY-MM-DD)
    - date_to: Filter to date (YYYY-MM-DD)
    """
    try:
        # Get query parameters
        page = int(request.GET.get("page", 1))
        limit = min(int(request.GET.get("limit", 10)), 100)
        status_filter = request.GET.get("status", "").strip()
        date_from = request.GET.get("date_from", "").strip()
        date_to = request.GET.get("date_to", "").strip()

        # Build filters
        filters = {}
        if status_filter:
            filters["status"] = status_filter
        if date_from:
            try:
                filters["date_from"] = datetime.strptime(date_from, "%Y-%m-%d").date()
            except ValueError:
                return standardize_response(
                    False,
                    "Invalid date_from format. Use YYYY-MM-DD",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        if date_to:
            try:
                filters["date_to"] = datetime.strptime(date_to, "%Y-%m-%d").date()
            except ValueError:
                return standardize_response(
                    False,
                    "Invalid date_to format. Use YYYY-MM-DD",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        # Get appointments based on user type
        if request.user.user_type == UserType.PATIENT.value:
            appointments_data = (
                AppointmentSelector.get_patient_appointments_with_pagination(
                    request.user.id, page, limit, filters
                )
            )
        elif request.user.user_type == UserType.DOCTOR.value:
            appointments_data = (
                AppointmentSelector.get_doctor_appointments_with_pagination(
                    request.user.id, page, limit, filters
                )
            )
        elif request.user.user_type == UserType.ADMIN.value:
            appointments_data = (
                AppointmentSelector.get_all_appointments_with_pagination(
                    page, limit, filters
                )
            )
        else:
            return standardize_response(
                False, "Invalid user type", status_code=status.HTTP_403_FORBIDDEN
            )

        return standardize_response(
            True,
            "Appointments retrieved successfully",
            appointments_data,
            status_code=status.HTTP_200_OK,
        )

    except ValueError as e:
        return standardize_response(
            False, "Invalid query parameters", status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Get appointments API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to retrieve appointments",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_appointment_detail(request, appointment_id):
    """
    Get specific appointment details
    GET /api/appointments/{appointment_id}/
    """
    try:
        appointment = AppointmentSelector.get_appointment_by_id(appointment_id)

        if not appointment:
            return standardize_response(
                False, "Appointment not found", status_code=status.HTTP_404_NOT_FOUND
            )

        # Authorization check
        can_view = False
        if request.user.user_type == UserType.ADMIN.value:
            can_view = True
        elif (
            request.user.user_type == UserType.PATIENT.value
            and request.user.id == appointment.patient.id
        ):
            can_view = True
        elif (
            request.user.user_type == UserType.DOCTOR.value
            and request.user.id == appointment.doctor.id
        ):
            can_view = True

        if not can_view:
            return standardize_response(
                False,
                "Insufficient permissions to view this appointment",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # Prepare appointment detail data
        appointment_datetime = timezone.make_aware(
            datetime.combine(appointment.appointment_date, appointment.appointment_time)
        )

        appointment_data = {
            "id": appointment.id,
            "patient": {
                "id": appointment.patient.id,
                "full_name": appointment.patient.full_name,
                "email": appointment.patient.email,
                "mobile": getattr(appointment.patient, "mobile", ""),
            },
            "doctor": {
                "id": appointment.doctor.id,
                "full_name": appointment.doctor.full_name,
                "license_number": getattr(appointment.doctor, "license_number", ""),
                "consultation_fee": float(
                    getattr(appointment.doctor, "consultation_fee", 0)
                ),
            },
            "appointment_date": appointment.appointment_date,
            "appointment_time": appointment.appointment_time,
            "appointment_datetime": appointment_datetime,
            "status": appointment.status,
            "consultation_fee": float(appointment.consultation_fee),
            "notes": appointment.notes,
            "created_at": appointment.created_at,
            "updated_at": appointment.updated_at,
        }

        return standardize_response(
            True,
            "Appointment details retrieved successfully",
            {"appointment": appointment_data},
            status_code=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Get appointment detail API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to retrieve appointment details",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_appointment_status(request, appointment_id):
    """
    Update appointment status
    PUT /api/appointments/{appointment_id}/status/

    Expected payload:
    {
        "status": "confirmed"  // pending, confirmed, completed, cancelled
    }
    """
    try:
        new_status = request.data.get("status", "").strip()

        if not new_status:
            return standardize_response(
                False, "Status is required", status_code=status.HTTP_400_BAD_REQUEST
            )

        # Update appointment status
        result = AppointmentServices.update_appointment_status(
            appointment_id, new_status, request.user.id
        )

        if result["success"]:
            logger.info(
                f"Appointment status updated via API: ID {appointment_id}, Status {new_status}, User {request.user.email}"
            )
            return standardize_response(
                True,
                result["message"],
                {
                    "appointment_id": result["appointment_id"],
                    "old_status": result["old_status"],
                    "new_status": result["new_status"],
                },
                status_code=status.HTTP_200_OK,
            )
        else:
            return standardize_response(
                False, result["message"], status_code=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        logger.error(f"Update appointment status API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to update appointment status",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def reschedule_appointment(request, appointment_id):
    """
    Reschedule an appointment
    PUT /api/appointments/{appointment_id}/reschedule/

    Expected payload:
    {
        "new_date": "2024-03-20",
        "new_time": "14:00"
    }
    """
    try:
        new_date = request.data.get("new_date", "").strip()
        new_time = request.data.get("new_time", "").strip()

        if not all([new_date, new_time]):
            return standardize_response(
                False,
                "New date and time are required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Reschedule appointment
        result = AppointmentServices.reschedule_appointment(
            appointment_id, new_date, new_time, request.user.id
        )

        if result["success"]:
            logger.info(
                f"Appointment rescheduled via API: ID {appointment_id}, User {request.user.email}"
            )
            return standardize_response(
                True,
                result["message"],
                {
                    "appointment_id": result["appointment_id"],
                    "old_datetime": result["old_datetime"],
                    "new_datetime": result["new_datetime"],
                },
                status_code=status.HTTP_200_OK,
            )
        else:
            return standardize_response(
                False, result["message"], status_code=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        logger.error(f"Reschedule appointment API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to reschedule appointment",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def cancel_appointment(request, appointment_id):
    """
    Cancel an appointment
    DELETE /api/appointments/{appointment_id}/

    Optional payload:
    {
        "cancellation_reason": "Emergency came up"
    }
    """
    try:
        cancellation_reason = request.data.get("cancellation_reason", "").strip()

        # Cancel appointment
        result = AppointmentServices.cancel_appointment(
            appointment_id, request.user.id, cancellation_reason
        )

        if result["success"]:
            logger.info(
                f"Appointment cancelled via API: ID {appointment_id}, User {request.user.email}"
            )
            return standardize_response(
                True,
                result["message"],
                {"appointment_id": result["appointment_id"]},
                status_code=status.HTTP_200_OK,
            )
        else:
            return standardize_response(
                False, result["message"], status_code=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        logger.error(f"Cancel appointment API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to cancel appointment",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_doctor_schedule(request, doctor_id=None):
    """
    Get doctor's schedule
    GET /api/appointments/schedule/{doctor_id}/
    OR
    GET /api/appointments/schedule/ (for doctor's own schedule)

    Query parameters:
    - date_from: Start date (YYYY-MM-DD, default: today)
    - date_to: End date (YYYY-MM-DD, default: today + 7 days)
    """
    try:
        # Determine which doctor's schedule to get
        if doctor_id:
            # Requesting specific doctor's schedule
            target_doctor_id = doctor_id
            # Only allow patients and admins to view other doctors' schedules
            if (
                request.user.user_type == UserType.DOCTOR.value
                and request.user.id != doctor_id
            ):
                return standardize_response(
                    False,
                    "Cannot view other doctors' schedules",
                    status_code=status.HTTP_403_FORBIDDEN,
                )
        else:
            # Requesting own schedule (only for doctors)
            if request.user.user_type != UserType.DOCTOR.value:
                return standardize_response(
                    False,
                    "Only doctors can view their own schedule without specifying doctor ID",
                    status_code=status.HTTP_403_FORBIDDEN,
                )
            target_doctor_id = request.user.id

        # Get date range
        date_from = request.GET.get("date_from", date.today().strftime("%Y-%m-%d"))
        date_to = request.GET.get(
            "date_to", (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")
        )

        # Get doctor schedule
        result = AppointmentServices.get_doctor_schedule(
            target_doctor_id, date_from, date_to
        )

        if result["success"]:
            return standardize_response(
                True,
                "Doctor schedule retrieved successfully",
                {"doctor_name": result["doctor_name"], "schedule": result["schedule"]},
                status_code=status.HTTP_200_OK,
            )
        else:
            return standardize_response(
                False, result["message"], status_code=status.HTTP_404_NOT_FOUND
            )

    except Exception as e:
        logger.error(f"Get doctor schedule API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to retrieve doctor schedule",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_patient_history(request, patient_id=None):
    """
    Get patient's appointment history
    GET /api/appointments/history/{patient_id}/
    OR
    GET /api/appointments/history/ (for patient's own history)

    Query parameters:
    - status: Filter by status
    """
    try:
        # Determine which patient's history to get
        if patient_id:
            # Requesting specific patient's history (Admin and Doctor can view)
            target_patient_id = patient_id
            if (
                request.user.user_type == UserType.PATIENT.value
                and request.user.id != patient_id
            ):
                return standardize_response(
                    False,
                    "Cannot view other patients' appointment history",
                    status_code=status.HTTP_403_FORBIDDEN,
                )
        else:
            # Requesting own history (only for patients)
            if request.user.user_type != UserType.PATIENT.value:
                return standardize_response(
                    False,
                    "Only patients can view their own history without specifying patient ID",
                    status_code=status.HTTP_403_FORBIDDEN,
                )
            target_patient_id = request.user.id

        # Get status filter
        status_filter = request.GET.get("status", "").strip()

        # Get patient appointment history
        result = AppointmentServices.get_patient_appointment_history(
            target_patient_id, status_filter
        )

        if result["success"]:
            return standardize_response(
                True,
                "Patient appointment history retrieved successfully",
                {
                    "patient_name": result["patient_name"],
                    "appointments": result["appointments"],
                    "statistics": result["statistics"],
                },
                status_code=status.HTTP_200_OK,
            )
        else:
            return standardize_response(
                False, result["message"], status_code=status.HTTP_404_NOT_FOUND
            )

    except Exception as e:
        logger.error(f"Get patient history API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to retrieve patient appointment history",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_available_slots(request, doctor_id):
    """
    Get available appointment slots for a doctor on a specific date
    GET /api/appointments/available-slots/{doctor_id}/

    Query parameters:
    - date: Date to check (YYYY-MM-DD, required)
    """
    try:
        appointment_date = request.GET.get("date", "").strip()

        if not appointment_date:
            return standardize_response(
                False,
                "Date parameter is required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Parse date
        try:
            check_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
        except ValueError:
            return standardize_response(
                False,
                "Invalid date format. Use YYYY-MM-DD",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Get doctor's available slots for the date
        available_slots = AppointmentSelector.get_doctor_available_slots(
            doctor_id, check_date
        )

        if available_slots is not None:
            return standardize_response(
                True,
                "Available slots retrieved successfully",
                {
                    "date": appointment_date,
                    "doctor_id": doctor_id,
                    "available_slots": available_slots["available_slots"],
                    "booked_slots": available_slots["booked_slots"],
                    "doctor_timeslots": available_slots["doctor_timeslots"],
                },
                status_code=status.HTTP_200_OK,
            )
        else:
            return standardize_response(
                False,
                "Doctor not found or has no available timeslots",
                status_code=status.HTTP_404_NOT_FOUND,
            )

    except Exception as e:
        logger.error(f"Get available slots API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to retrieve available slots",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_appointment_statistics(request):
    """
    Get appointment statistics for dashboard
    GET /api/appointments/statistics/

    Returns different stats based on user type:
    - Patient: Their appointment stats
    - Doctor: Their practice stats
    - Admin: System-wide stats
    """
    try:
        if request.user.user_type == UserType.PATIENT.value:
            # Patient statistics
            stats = AppointmentSelector.get_patient_appointment_statistics(
                request.user.id
            )
        elif request.user.user_type == UserType.DOCTOR.value:
            # Doctor statistics
            stats = AppointmentSelector.get_doctor_appointment_statistics(
                request.user.id
            )
        elif request.user.user_type == UserType.ADMIN.value:
            # Admin statistics
            stats = AppointmentSelector.get_admin_appointment_statistics()
        else:
            return standardize_response(
                False, "Invalid user type", status_code=status.HTTP_403_FORBIDDEN
            )

        return standardize_response(
            True,
            "Appointment statistics retrieved successfully",
            {"statistics": stats},
            status_code=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Get appointment statistics API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to retrieve appointment statistics",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Admin-only endpoints
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_appointments_admin(request):
    """
    Get all appointments for admin with advanced filtering
    GET /api/appointments/admin/all/

    Query parameters:
    - page, limit: Pagination
    - status, doctor_id, patient_id: Filters
    - date_from, date_to: Date range
    - search: Search in patient/doctor names
    """
    try:
        # Check admin permission
        if request.user.user_type != UserType.ADMIN.value:
            return standardize_response(
                False,
                "Admin privileges required",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # Get query parameters
        page = int(request.GET.get("page", 1))
        limit = min(int(request.GET.get("limit", 20)), 100)

        # Build advanced filters
        filters = {}
        for param in [
            "status",
            "doctor_id",
            "patient_id",
            "date_from",
            "date_to",
            "search",
        ]:
            value = request.GET.get(param, "").strip()
            if value:
                filters[param] = value

        # Get appointments with advanced filters
        appointments_data = AppointmentSelector.get_admin_appointments_with_filters(
            page, limit, filters
        )

        return standardize_response(
            True,
            "All appointments retrieved successfully",
            appointments_data,
            status_code=status.HTTP_200_OK,
        )

    except ValueError as e:
        return standardize_response(
            False, "Invalid query parameters", status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Get all appointments admin API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to retrieve appointments",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

import json
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .selectors import DoctorSelector, UserSelector
from .services import UserServices

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
@permission_classes([AllowAny])
def register_user(request):
    """
    User registration endpoint
    POST /api/users/register/

    Expected payload:
    {
        "email": "user@example.com",
        "mobile_number": "+8801712345678",
        "password": "StrongPass123!",
        "full_name": "John Doe",
        "user_type": "patient",
        "division_id": 1,
        "district_id": 1,
        "thana_id": 1,
        "profile_image": <file>,
        // For doctors only:
        "license_number": "DOC12345",
        "experience_years": 5,
        "consultation_fee": 500.00,
        "available_timeslots": ["10:00-11:00", "14:00-15:00"]
    }
    """
    try:
        # Handle both JSON and form data
        if request.content_type == "application/json":
            user_data = json.loads(request.body)
        else:
            user_data = request.data.dict()

        # Handle file upload (profile_image)
        if "profile_image" in request.FILES:
            user_data["profile_image"] = request.FILES["profile_image"]

        # Handle timeslots for doctors (convert from JSON string if needed)
        if "available_timeslots" in user_data and isinstance(
            user_data["available_timeslots"], str
        ):
            try:
                user_data["available_timeslots"] = json.loads(
                    user_data["available_timeslots"]
                )
            except json.JSONDecodeError:
                return standardize_response(
                    False,
                    "Invalid timeslots format",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        # Convert numeric fields
        for field in ["experience_years"]:
            if field in user_data and user_data[field]:
                try:
                    user_data[field] = int(user_data[field])
                except (ValueError, TypeError):
                    return standardize_response(
                        False,
                        f"Invalid {field} format",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )

        if "consultation_fee" in user_data and user_data["consultation_fee"]:
            try:
                user_data["consultation_fee"] = float(user_data["consultation_fee"])
            except (ValueError, TypeError):
                return standardize_response(
                    False,
                    "Invalid consultation fee format",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        # Register user
        result = UserServices.register_user(user_data)

        if result["success"]:
            logger.info(
                f"User registered successfully via API: {user_data.get('email')}"
            )
            return standardize_response(
                True,
                result["message"],
                {"user_id": result["user_id"], "user_type": result["user_type"]},
                status_code=status.HTTP_201_CREATED,
            )
        else:
            return standardize_response(
                False, result["message"], status_code=status.HTTP_400_BAD_REQUEST
            )

    except json.JSONDecodeError:
        return standardize_response(
            False, "Invalid JSON format", status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Registration API error: {str(e)}")
        return standardize_response(
            False,
            "Registration failed due to server error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def login_user(request):
    """
    User login endpoint
    POST /api/users/login/

    Expected payload:
    {
        "email": "user@example.com",
        "password": "password123"
    }
    """
    try:
        email = request.data.get("email", "").strip()
        password = request.data.get("password", "")

        if not email or not password:
            return standardize_response(
                False,
                "Email and password are required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Authenticate user
        result = UserServices.authenticate_user(email, password)

        if result["success"]:
            logger.info(f"User logged in successfully: {email}")
            return standardize_response(
                True,
                result["message"],
                {
                    "access_token": result["access_token"],
                    "refresh_token": result["refresh_token"],
                    "user": result["user"],
                },
                status_code=status.HTTP_200_OK,
            )
        else:
            return standardize_response(
                False, result["message"], status_code=status.HTTP_401_UNAUTHORIZED
            )

    except Exception as e:
        logger.error(f"Login API error: {str(e)}")
        return standardize_response(
            False,
            "Login failed due to server error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """
    User logout endpoint
    POST /api/users/logout/

    Expected payload:
    {
        "refresh_token": "refresh_token_here"
    }
    """
    try:
        refresh_token = request.data.get("refresh_token")

        if refresh_token:
            try:
                # Blacklist the refresh token
                token = RefreshToken(refresh_token)
                token.blacklist()

                logger.info(f"User logged out successfully: {request.user.email}")
                return standardize_response(
                    True, "Logout successful", status_code=status.HTTP_200_OK
                )
            except Exception as e:
                logger.warning(f"Token blacklist error: {str(e)}")
                return standardize_response(
                    True,
                    "Logout successful (token may already be invalid)",
                    status_code=status.HTTP_200_OK,
                )
        else:
            return standardize_response(
                True, "Logout successful", status_code=status.HTTP_200_OK
            )

    except Exception as e:
        logger.error(f"Logout API error: {str(e)}")
        return standardize_response(
            False,
            "Logout failed due to server error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """
    Get user profile endpoint
    GET /api/users/profile/
    """
    try:
        user = UserSelector.get_user_by_id(request.user.id)

        if not user:
            return standardize_response(
                False, "User not found", status_code=status.HTTP_404_NOT_FOUND
            )

        # Prepare user profile data
        profile_data = {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "mobile_number": user.mobile_number,
            "user_type": user.user_type,
            "profile_image": user.profile_image.url if user.profile_image else None,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "last_login": user.last_login,
        }

        # Add location data
        if user.division:
            profile_data["location"] = {
                "division": {"id": user.division.id, "name": user.division.name},
                "district": (
                    {"id": user.district.id, "name": user.district.name}
                    if user.district
                    else None
                ),
                "thana": (
                    {"id": user.thana.id, "name": user.thana.name}
                    if user.thana
                    else None
                ),
            }

        # Add doctor-specific data
        if user.user_type == "doctor":
            profile_data["doctor_info"] = {
                "license_number": user.license_number,
                "experience_years": user.experience_years,
                "consultation_fee": user.consultation_fee,
                "available_timeslots": user.available_timeslots,
            }

        return standardize_response(
            True,
            "Profile retrieved successfully",
            {"profile": profile_data},
            status_code=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Get profile API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to retrieve profile",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    """
    Update user profile endpoint
    PUT/PATCH /api/users/profile/

    Expected payload (any combination of these fields):
    {
        "full_name": "New Name",
        "mobile_number": "+8801712345678",
        "division_id": 1,
        "district_id": 1,
        "thana_id": 1,
        "profile_image": <file>,
        // For doctors only:
        "experience_years": 5,
        "consultation_fee": 600.00,
        "available_timeslots": ["10:00-11:00", "15:00-16:00"]
    }
    """
    try:
        # Handle both JSON and form data
        if request.content_type == "application/json":
            update_data = json.loads(request.body)
        else:
            update_data = request.data.dict()

        # Handle file upload (profile_image)
        if "profile_image" in request.FILES:
            update_data["profile_image"] = request.FILES["profile_image"]

        # Handle timeslots for doctors (convert from JSON string if needed)
        if "available_timeslots" in update_data and isinstance(
            update_data["available_timeslots"], str
        ):
            try:
                update_data["available_timeslots"] = json.loads(
                    update_data["available_timeslots"]
                )
            except json.JSONDecodeError:
                return standardize_response(
                    False,
                    "Invalid timeslots format",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        # Convert numeric fields
        for field in ["experience_years"]:
            if field in update_data and update_data[field]:
                try:
                    update_data[field] = int(update_data[field])
                except (ValueError, TypeError):
                    return standardize_response(
                        False,
                        f"Invalid {field} format",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )

        if "consultation_fee" in update_data and update_data["consultation_fee"]:
            try:
                update_data["consultation_fee"] = float(update_data["consultation_fee"])
            except (ValueError, TypeError):
                return standardize_response(
                    False,
                    "Invalid consultation fee format",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        # Update profile
        result = UserServices.update_user_profile(request.user.id, update_data)

        if result["success"]:
            logger.info(f"User profile updated via API: {request.user.email}")
            return standardize_response(
                True,
                result["message"],
                {"updated_fields": result["updated_fields"]},
                status_code=status.HTTP_200_OK,
            )
        else:
            return standardize_response(
                False, result["message"], status_code=status.HTTP_400_BAD_REQUEST
            )

    except json.JSONDecodeError:
        return standardize_response(
            False, "Invalid JSON format", status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Update profile API error: {str(e)}")
        return standardize_response(
            False,
            "Profile update failed due to server error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change password endpoint
    POST /api/users/change-password/

    Expected payload:
    {
        "old_password": "current_password",
        "new_password": "new_password123"
    }
    """
    try:
        old_password = request.data.get("old_password", "")
        new_password = request.data.get("new_password", "")

        if not old_password or not new_password:
            return standardize_response(
                False,
                "Both old and new passwords are required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Change password
        result = UserServices.change_password(
            request.user.id, old_password, new_password
        )

        if result["success"]:
            logger.info(f"Password changed via API: {request.user.email}")
            return standardize_response(
                True, result["message"], status_code=status.HTTP_200_OK
            )
        else:
            return standardize_response(
                False, result["message"], status_code=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        logger.error(f"Change password API error: {str(e)}")
        return standardize_response(
            False,
            "Password change failed due to server error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_dashboard(request):
    """
    Get user dashboard data endpoint
    GET /api/users/dashboard/
    """
    try:
        result = UserServices.get_user_dashboard_data(request.user.id)

        if result["success"]:
            return standardize_response(
                True,
                "Dashboard data retrieved successfully",
                result["data"],
                status_code=status.HTTP_200_OK,
            )
        else:
            return standardize_response(
                False, result["message"], status_code=status.HTTP_404_NOT_FOUND
            )

    except Exception as e:
        logger.error(f"Dashboard API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to retrieve dashboard data",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_doctors_list(request):
    """
    Get doctors list with filtering and pagination
    GET /api/users/doctors/

    Query parameters:
    - page: Page number (default: 1)
    - limit: Items per page (default: 10)
    - search: Search by name or license number
    - experience_min: Minimum experience years
    - experience_max: Maximum experience years
    - fee_min: Minimum consultation fee
    - fee_max: Maximum consultation fee
    - division_id: Filter by division
    - district_id: Filter by district
    - thana_id: Filter by thana
    """
    try:
        # Get query parameters
        page = int(request.GET.get("page", 1))
        limit = min(int(request.GET.get("limit", 10)), 100)  # Max 100 items per page
        search = request.GET.get("search", "").strip()

        # Experience filters
        experience_min = request.GET.get("experience_min")
        experience_max = request.GET.get("experience_max")

        # Fee filters
        fee_min = request.GET.get("fee_min")
        fee_max = request.GET.get("fee_max")

        # Location filters
        division_id = request.GET.get("division_id")
        district_id = request.GET.get("district_id")
        thana_id = request.GET.get("thana_id")

        # Build filters dictionary
        filters = {}

        if search:
            filters["search"] = search

        if experience_min:
            try:
                filters["experience_years__gte"] = int(experience_min)
            except ValueError:
                pass

        if experience_max:
            try:
                filters["experience_years__lte"] = int(experience_max)
            except ValueError:
                pass

        if fee_min:
            try:
                filters["consultation_fee__gte"] = float(fee_min)
            except ValueError:
                pass

        if fee_max:
            try:
                filters["consultation_fee__lte"] = float(fee_max)
            except ValueError:
                pass

        if division_id:
            try:
                filters["division_id"] = int(division_id)
            except ValueError:
                pass

        if district_id:
            try:
                filters["district_id"] = int(district_id)
            except ValueError:
                pass

        if thana_id:
            try:
                filters["thana_id"] = int(thana_id)
            except ValueError:
                pass

        # Get doctors with pagination
        doctors_data = DoctorSelector.get_doctors_with_pagination(
            page=page, limit=limit, filters=filters
        )

        # Serialize doctors data
        serialized_data = {
            "total": doctors_data["total"],
            "pages": doctors_data["pages"],
            "current_page": doctors_data["current_page"],
            "doctors": [
                {
                    "id": doctor.id,
                    "full_name": doctor.user.full_name,
                    "email": doctor.user.email,
                    "mobile_number": doctor.user.mobile_number,
                    "profile_image": (
                        doctor.user.profile_image.url
                        if doctor.user.profile_image
                        else None
                    ),
                    "license_number": doctor.license_number,
                    "experience_years": doctor.experience_years,
                    "consultation_fee": doctor.consultation_fee,
                    "available_timeslots": DoctorSelector.get_doctor_available_slots(
                        doctor.id
                    ),
                    "location": {
                        "division": (
                            {
                                "id": doctor.user.division.id,
                                "name": doctor.user.division.name,
                            }
                            if doctor.user.division
                            else None
                        ),
                        "district": (
                            {
                                "id": doctor.user.district.id,
                                "name": doctor.user.district.name,
                            }
                            if doctor.user.district
                            else None
                        ),
                        "thana": (
                            {"id": doctor.user.thana.id, "name": doctor.user.thana.name}
                            if doctor.user.thana
                            else None
                        ),
                    },
                }
                for doctor in doctors_data["doctors"]
            ],
        }

        return standardize_response(
            True,
            "Doctors list retrieved successfully",
            serialized_data,
            status_code=status.HTTP_200_OK,
        )

    except ValueError as e:
        return standardize_response(
            False, "Invalid query parameters", status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Get doctors list API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to retrieve doctors list",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_doctor_detail(request, doctor_id):
    """
    Get doctor detail endpoint
    GET /api/users/doctors/{doctor_id}/
    """
    try:
        doctor = DoctorSelector.get_doctor_by_id(doctor_id)
        if not doctor:
            return standardize_response(
                False, "Doctor not found", status_code=status.HTTP_404_NOT_FOUND
            )

        # Prepare doctor detail data
        doctor_data = {
            "id": doctor.id,
            "full_name": doctor.user.full_name,
            "email": doctor.user.email,
            "mobile_number": doctor.user.mobile_number,
            "profile_image": (
                doctor.user.profile_image.url if doctor.user.profile_image else None
            ),
            "license_number": doctor.license_number,
            "experience_years": doctor.experience_years,
            "consultation_fee": doctor.consultation_fee,
            "available_timeslots": DoctorSelector.get_doctor_available_slots(doctor.id),
            "created_at": doctor.created_at,
        }

        # Add location data
        if doctor.user.division:
            doctor_data["location"] = {
                "division": {
                    "id": doctor.user.division.id,
                    "name": doctor.user.division.name,
                },
                "district": (
                    {"id": doctor.user.district.id, "name": doctor.user.district.name}
                    if doctor.user.district
                    else None
                ),
                "thana": (
                    {"id": doctor.user.thana.id, "name": doctor.user.thana.name}
                    if doctor.user.thana
                    else None
                ),
            }

        return standardize_response(
            True,
            "Doctor details retrieved successfully",
            {"doctor": doctor_data},
            status_code=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Get doctor detail API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to retrieve doctor details",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Admin only endpoints
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_users_list(request):
    """
    Get users list for admin (Admin only)
    GET /api/users/admin/users/
    """
    try:
        # Check if user is admin
        if request.user.user_type != "admin":
            return standardize_response(
                False,
                "Access denied. Admin privileges required.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # Get query parameters
        page = int(request.GET.get("page", 1))
        limit = min(int(request.GET.get("limit", 10)), 100)
        user_type = request.GET.get("user_type", "")
        search = request.GET.get("search", "").strip()

        # Build filters
        filters = {
            "user_type": (
                user_type if user_type in ["patient", "doctor", "admin"] else None
            ),
            "search": search if search else None,
        }

        # Get users with pagination
        users_data = UserSelector.get_users_with_pagination(
            page=page, limit=limit, filters=filters
        )

        # Serialize users data
        serialized_data = {
            "total": users_data["total"],
            "pages": users_data["pages"],
            "current_page": users_data["current_page"],
            "users": [
                {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "mobile_number": user.mobile_number,
                    "user_type": user.user_type,
                    "profile_image": (
                        user.profile_image.url if user.profile_image else None
                    ),
                    "created_at": user.created_at,
                    "last_login": user.last_login,
                }
                for user in users_data["users"]
            ],
        }

        return standardize_response(
            True,
            "Users list retrieved successfully",
            serialized_data,
            status_code=status.HTTP_200_OK,
        )

    except ValueError:
        return standardize_response(
            False, "Invalid query parameters", status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Get users list API error: {str(e)}")
        return standardize_response(
            False,
            "Failed to retrieve users list",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

import re
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import transaction
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from PIL import Image
import logging

from .models import User
from .selectors import UserSelector, DoctorSelector, PatientSelector
from appointment.selectors import AppointmentSelector

from location.selectors import LocationSelector

logger = logging.getLogger(__name__)


class UserValidationError(Exception):
    """Custom exception for user validation errors"""

    pass


class UserServices:
    """Service class for user-related business operations"""

    @staticmethod
    def validate_mobile_number(mobile: str) -> bool:
        """
        Validate mobile number format (+88 and exactly 14 digits)
        Example: +8801712345678
        """
        pattern = r"^\+88\d{11}$"
        return bool(re.match(pattern, mobile))

    @staticmethod
    def validate_password(password: str) -> Tuple[bool, List[str]]:
        """
        Validate password strength
        Requirements: minimum 8 characters, 1 uppercase, 1 digit, 1 special character
        """
        errors = []

        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")

        if not re.search(r"\d", password):
            errors.append("Password must contain at least one digit")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")

        return len(errors) == 0, errors

    @staticmethod
    def validate_profile_image(image_file) -> Tuple[bool, str]:
        """
        Validate profile image (max 5MB, JPEG/PNG only)
        """
        if not image_file:
            return True, ""

        # Check file size (5MB = 5 * 1024 * 1024 bytes)
        max_size = 5 * 1024 * 1024
        if image_file.size > max_size:
            return False, "Image file size must be less than 5MB"

        # Check MIME type
        allowed_types = ["image/jpeg", "image/jpg", "image/png"]
        if image_file.content_type not in allowed_types:
            return False, "Only JPEG and PNG images are allowed"

        return True, ""

    @staticmethod
    def validate_doctor_timeslots(timeslots: List[str]) -> Tuple[bool, List[str]]:
        """
        Validate doctor timeslots format
        Expected format: ["10:00-11:00", "14:00-15:00"]
        """
        errors = []
        time_pattern = r"^\d{2}:\d{2}-\d{2}:\d{2}$"

        for slot in timeslots:
            if not re.match(time_pattern, slot):
                errors.append(
                    f"Invalid timeslot format: {slot}. Use HH:MM-HH:MM format"
                )
                continue

            try:
                start_time, end_time = slot.split("-")
                start_hour, start_min = map(int, start_time.split(":"))
                end_hour, end_min = map(int, end_time.split(":"))

                # Validate time ranges
                if not (0 <= start_hour <= 23 and 0 <= start_min <= 59):
                    errors.append(f"Invalid start time in slot: {slot}")

                if not (0 <= end_hour <= 23 and 0 <= end_min <= 59):
                    errors.append(f"Invalid end time in slot: {slot}")

                # Check if start time is before end time
                start_minutes = start_hour * 60 + start_min
                end_minutes = end_hour * 60 + end_min

                if start_minutes >= end_minutes:
                    errors.append(f"Start time must be before end time in slot: {slot}")

            except ValueError:
                errors.append(f"Invalid time format in slot: {slot}")

        return len(errors) == 0, errors

    @staticmethod
    def process_profile_image(image_file, user_id: int) -> Optional[str]:
        """
        Process and save profile image
        Returns the file path or None if no image
        """
        if not image_file:
            return None

        try:
            # Generate unique filename
            file_extension = os.path.splitext(image_file.name)[1]
            filename = f"profile_{user_id}_{uuid.uuid4().hex[:8]}{file_extension}"
            filepath = f"profiles/{filename}"

            # Open and process image with PIL (optional: resize, optimize)
            image = Image.open(image_file)

            # Optional: Resize image if too large (e.g., max 800x800)
            if image.width > 800 or image.height > 800:
                image.thumbnail((800, 800), Image.Resampling.LANCZOS)

            # Save processed image
            from io import BytesIO

            output = BytesIO()
            format_type = (
                "JPEG" if file_extension.lower() in [".jpg", ".jpeg"] else "PNG"
            )
            image.save(output, format=format_type, quality=85, optimize=True)
            output.seek(0)

            # Save to storage
            saved_path = default_storage.save(filepath, ContentFile(output.read()))
            logger.info(f"Profile image saved: {saved_path}")

            return saved_path

        except Exception as e:
            logger.error(f"Error processing profile image: {str(e)}")
            raise UserValidationError(f"Error processing profile image: {str(e)}")

    @classmethod
    def register_user(cls, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new user with comprehensive validation
        """
        try:
            with transaction.atomic():
                # Extract and validate required fields
                email = user_data.get("email", "").strip().lower()
                mobile = user_data.get("mobile", "").strip()
                password = user_data.get("password", "")
                user_type = user_data.get("user_type", "")
                full_name = user_data.get("full_name", "").strip()

                # Basic field validation
                if not all([email, mobile, password, user_type, full_name]):
                    raise UserValidationError("All required fields must be provided")

                # Email validation
                if not re.match(
                    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email
                ):
                    raise UserValidationError("Invalid email format")

                # Check unique email and mobile
                if UserSelector.get_user_by_email(email):
                    raise UserValidationError("Email already exists")

                if UserSelector.get_user_by_mobile(mobile):
                    raise UserValidationError("Mobile number already exists")

                # Mobile number validation
                if not cls.validate_mobile_number(mobile):
                    raise UserValidationError(
                        "Mobile number must be in +88 format with 11 digits"
                    )

                # Password validation
                is_valid_password, password_errors = cls.validate_password(password)
                if not is_valid_password:
                    raise UserValidationError("; ".join(password_errors))

                # User type validation
                if user_type not in [choice[0] for choice in User.USER_TYPE_CHOICES]:
                    raise UserValidationError("Invalid user type")

                # Location validation
                division_id = user_data.get("division_id")
                district_id = user_data.get("district_id")
                thana_id = user_data.get("thana_id")

                if division_id:
                    if not LocationSelector.get_division_by_id(division_id):
                        raise UserValidationError("Invalid division")

                if district_id:
                    district = LocationSelector.get_district_by_id(district_id)
                    if not district or district.division_id != division_id:
                        raise UserValidationError(
                            "Invalid district for selected division"
                        )

                if thana_id:
                    thana = LocationSelector.get_thana_by_id(thana_id)
                    if not thana or thana.district_id != district_id:
                        raise UserValidationError("Invalid thana for selected district")

                # Profile image validation
                profile_image = user_data.get("profile_image")
                if profile_image:
                    is_valid_image, image_error = cls.validate_profile_image(
                        profile_image
                    )
                    if not is_valid_image:
                        raise UserValidationError(image_error)

                # Doctor-specific validation
                if user_type == User.DOCTOR:
                    license_number = user_data.get("license_number", "").strip()
                    experience_years = user_data.get("experience_years")
                    consultation_fee = user_data.get("consultation_fee")
                    available_timeslots = user_data.get("available_timeslots", [])

                    if not license_number:
                        raise UserValidationError(
                            "License number is required for doctors"
                        )

                    if not experience_years or experience_years < 0:
                        raise UserValidationError(
                            "Valid experience years is required for doctors"
                        )

                    if not consultation_fee or consultation_fee <= 0:
                        raise UserValidationError(
                            "Valid consultation fee is required for doctors"
                        )

                    if not available_timeslots:
                        raise UserValidationError(
                            "Available timeslots are required for doctors"
                        )

                    # Validate timeslots
                    is_valid_timeslots, timeslot_errors = cls.validate_doctor_timeslots(
                        available_timeslots
                    )
                    if not is_valid_timeslots:
                        raise UserValidationError("; ".join(timeslot_errors))

                    # Check unique license number
                    if DoctorSelector.get_doctor_by_license(license_number):
                        raise UserValidationError("License number already exists")

                # Create user
                user = User.objects.create(
                    email=email,
                    mobile=mobile,
                    password=make_password(password),
                    user_type=user_type,
                    full_name=full_name,
                    division_id=division_id,
                    district_id=district_id,
                    thana_id=thana_id,
                    is_active=True,
                )

                # Handle profile image
                if profile_image:
                    image_path = cls.process_profile_image(profile_image, user.id)
                    if image_path:
                        user.profile_image = image_path
                        user.save(update_fields=["profile_image"])

                # Handle doctor-specific fields
                if user_type == User.DOCTOR:
                    user.license_number = license_number
                    user.experience_years = experience_years
                    user.consultation_fee = consultation_fee
                    user.available_timeslots = available_timeslots
                    user.save(
                        update_fields=[
                            "license_number",
                            "experience_years",
                            "consultation_fee",
                            "available_timeslots",
                        ]
                    )

                logger.info(f"User registered successfully: {email}")

                return {
                    "success": True,
                    "message": "User registered successfully",
                    "user_id": user.id,
                    "user_type": user.user_type,
                }

        except UserValidationError as e:
            logger.warning(f"User registration validation error: {str(e)}")
            return {"success": False, "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error during user registration: {str(e)}")
            return {
                "success": False,
                "message": "Registration failed due to server error",
            }

    @staticmethod
    def authenticate_user(email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user and generate JWT tokens
        """
        try:
            email = email.strip().lower()

            if not email or not password:
                return {"success": False, "message": "Email and password are required"}

            # Authenticate user
            user = authenticate(username=email, password=password)

            if not user:
                # Check if user exists to provide appropriate error
                if not UserSelector.get_user_by_email(email):
                    message = "User with this email does not exist"
                else:
                    message = "Invalid password"

                return {"success": False, "message": message}

            if not user.is_active:
                return {"success": False, "message": "Account is inactive"}

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Update last login
            user.last_login = datetime.now()
            user.save(update_fields=["last_login"])

            logger.info(f"User authenticated successfully: {email}")

            return {
                "success": True,
                "message": "Login successful",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "user_type": user.user_type,
                    "mobile": user.mobile,
                    "profile_image": (
                        user.profile_image.url if user.profile_image else None
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return {
                "success": False,
                "message": "Authentication failed due to server error",
            }

    @classmethod
    def update_user_profile(
        cls, user_id: int, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update user profile with validation
        """
        try:
            with transaction.atomic():
                user = UserSelector.get_user_by_id(user_id)
                if not user:
                    return {"success": False, "message": "User not found"}

                # Fields that can be updated
                updatable_fields = [
                    "full_name",
                    "mobile",
                    "division_id",
                    "district_id",
                    "thana_id",
                ]

                # Doctor-specific updatable fields
                if user.user_type == User.DOCTOR:
                    updatable_fields.extend(
                        ["experience_years", "consultation_fee", "available_timeslots"]
                    )

                updated_fields = []

                # Validate and update each field
                for field, value in update_data.items():
                    if field not in updatable_fields:
                        continue

                    if field == "mobile" and value:
                        value = value.strip()
                        if not cls.validate_mobile_number(value):
                            raise UserValidationError("Invalid mobile number format")

                        # Check if mobile is unique (excluding current user)
                        existing_user = UserSelector.get_user_by_mobile(value)
                        if existing_user and existing_user.id != user_id:
                            raise UserValidationError("Mobile number already exists")

                    elif field == "available_timeslots" and value:
                        is_valid, errors = cls.validate_doctor_timeslots(value)
                        if not is_valid:
                            raise UserValidationError("; ".join(errors))

                    elif (
                        field in ["experience_years", "consultation_fee"]
                        and value is not None
                    ):
                        if value < 0:
                            raise UserValidationError(
                                f"Invalid {field.replace('_', ' ')}"
                            )

                    # Location validation
                    elif field == "division_id" and value:
                        if not LocationSelector.get_division_by_id(value):
                            raise UserValidationError("Invalid division")

                    elif field == "district_id" and value:
                        division_id = update_data.get("division_id", user.division_id)
                        district = LocationSelector.get_district_by_id(value)
                        if not district or district.division_id != division_id:
                            raise UserValidationError(
                                "Invalid district for selected division"
                            )

                    elif field == "thana_id" and value:
                        district_id = update_data.get("district_id", user.district_id)
                        thana = LocationSelector.get_thana_by_id(value)
                        if not thana or thana.district_id != district_id:
                            raise UserValidationError(
                                "Invalid thana for selected district"
                            )

                    # Update field
                    setattr(user, field, value)
                    updated_fields.append(field)

                # Handle profile image update
                if "profile_image" in update_data:
                    profile_image = update_data["profile_image"]
                    if profile_image:
                        is_valid_image, image_error = cls.validate_profile_image(
                            profile_image
                        )
                        if not is_valid_image:
                            raise UserValidationError(image_error)

                        # Delete old image if exists
                        if user.profile_image:
                            try:
                                default_storage.delete(user.profile_image.name)
                            except Exception as e:
                                logger.warning(
                                    f"Could not delete old profile image: {str(e)}"
                                )

                        # Process and save new image
                        image_path = cls.process_profile_image(profile_image, user.id)
                        if image_path:
                            user.profile_image = image_path
                            updated_fields.append("profile_image")

                # Save user if any fields were updated
                if updated_fields:
                    user.updated_at = datetime.now()
                    updated_fields.append("updated_at")
                    user.save(update_fields=updated_fields)

                logger.info(
                    f"User profile updated: {user.email}, fields: {updated_fields}"
                )

                return {
                    "success": True,
                    "message": "Profile updated successfully",
                    "updated_fields": updated_fields,
                }

        except UserValidationError as e:
            logger.warning(f"Profile update validation error: {str(e)}")
            return {"success": False, "message": str(e)}
        except Exception as e:
            logger.error(f"Profile update error: {str(e)}")
            return {
                "success": False,
                "message": "Profile update failed due to server error",
            }

    @staticmethod
    def change_password(
        user_id: int, old_password: str, new_password: str
    ) -> Dict[str, Any]:
        """
        Change user password with validation
        """
        try:
            user = UserSelector.get_user_by_id(user_id)
            if not user:
                return {"success": False, "message": "User not found"}

            # Verify old password
            if not user.check_password(old_password):
                return {"success": False, "message": "Current password is incorrect"}

            # Validate new password
            is_valid_password, password_errors = UserServices.validate_password(
                new_password
            )
            if not is_valid_password:
                return {"success": False, "message": "; ".join(password_errors)}

            # Update password
            user.set_password(new_password)
            user.updated_at = datetime.now()
            user.save(update_fields=["password", "updated_at"])

            logger.info(f"Password changed successfully for user: {user.email}")

            return {"success": True, "message": "Password changed successfully"}

        except Exception as e:
            logger.error(f"Password change error: {str(e)}")
            return {
                "success": False,
                "message": "Password change failed due to server error",
            }

    @staticmethod
    def get_user_dashboard_data(user_id: int) -> Dict[str, Any]:
        """
        Get user-specific dashboard data based on user type
        """
        try:
            user = UserSelector.get_user_by_id(user_id)
            if not user:
                return {"success": False, "message": "User not found"}

            dashboard_data = {
                "user_info": {
                    "id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "user_type": user.user_type,
                    "mobile": user.mobile,
                    "profile_image": (
                        user.profile_image.url if user.profile_image else None
                    ),
                    "last_login": user.last_login,
                }
            }

            # Add user-type specific data
            if user.user_type == User.PATIENT:
                # Add patient-specific dashboard data
                dashboard_data["stats"] = {
                    "total_appointments": 0,  # Will be filled by appointment service
                    "upcoming_appointments": 0,
                    "completed_appointments": 0,
                }

            elif user.user_type == User.DOCTOR:
                # Add doctor-specific dashboard data
                dashboard_data["doctor_info"] = {
                    "license_number": user.license_number,
                    "experience_years": user.experience_years,
                    "consultation_fee": user.consultation_fee,
                    "available_timeslots": user.available_timeslots,
                }
                dashboard_data["stats"] = {
                    "total_patients": 0,  # Will be filled by appointment service
                    "today_appointments": 0,
                    "this_month_earnings": 0,
                }

            elif user.user_type == User.ADMIN:
                # Add admin-specific dashboard data
                dashboard_data["stats"] = {
                    "total_users": UserSelector.get_total_users_count(),
                    "total_doctors": DoctorSelector.get_doctors_count(),
                    "total_patients": PatientSelector.get_patients_count(),
                    "total_appointments": AppointmentSelector.get_appointments_count(),
                }

            return {"success": True, "data": dashboard_data}

        except Exception as e:
            logger.error(f"Dashboard data retrieval error: {str(e)}")
            return {"success": False, "message": "Failed to retrieve dashboard data"}

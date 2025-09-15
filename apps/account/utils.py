import os

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


def validate_image_size(image):
    """Validate image file size (max 5MB)"""
    if image.size > 5 * 1024 * 1024:  # 5MB
        raise ValidationError("Image file too large ( > 5MB )")


def user_profile_image_path(instance, filename):
    """Generate path for user profile images"""
    ext = filename.split(".")[-1]
    filename = f"{instance.id}_profile.{ext}"
    return os.path.join("profile_images", filename)


def phone_validator():
    """
    Returns a RegexValidator for Bangladeshi phone numbers.
    Format: +88XXXXXXXXXXX (11 digits after +88)
    """
    return RegexValidator(
        regex=r"^\+88\d{11}$",
        message="Phone number must be in format: '+88' followed by 11 digits.",
    )

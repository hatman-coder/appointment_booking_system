from enum import Enum


class BaseEnum(Enum):
    """
    Global Enum base class with utility methods:
    - choices(): for Django model field choices
    - value_list(): returns all enum values
    - value(): returns the value of an enum instance
    """

    def __str__(self):
        # Default human-readable label
        return self.name.capitalize()

    @classmethod
    def choices(cls):
        """
        Returns a list of tuples for Django model fields:
        [(value, label), ...]
        """
        return [(member.value, str(member)) for member in cls]

    @classmethod
    def value_list(cls):
        """
        Returns a list of all enum values:
        [value1, value2, ...]
        """
        return [member.value for member in cls]

    def __call__(self):
        """
        Makes enum instances callable to return their value.
        Example: UserType.PATIENT() -> "patient"
        """
        return self.value()

    @property
    def value(self):
        """
        Property decorator to allow using .value instead of .value()
        Example: UserType.PATIENT.value -> "patient"
        """
        return self._value_


class UserType(BaseEnum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"


class AppointmentStatus(BaseEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

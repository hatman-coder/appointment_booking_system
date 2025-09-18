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

    def value(self):
        """
        Return the actual value of the enum instance.
        Example: UserType.PATIENT.value() -> "patient"
        """
        return self._value_

    @classmethod
    def choices(cls):
        """
        Returns a list of tuples for Django model fields:
        [(value, label), ...]
        """
        return [(member.value(), str(member)) for member in cls]

    @classmethod
    def value_list(cls):
        """
        Returns a list of all enum values:
        [value1, value2, ...]
        """
        return [member.value() for member in cls]


class UserType(BaseEnum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"


class AppointmentStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

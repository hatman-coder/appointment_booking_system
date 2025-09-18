import uuid
from django.db.models import *


class ActiveManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class DeactivateManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=False)


class BaseModel(Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    is_active = BooleanField(default=True, editable=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    objects = Manager()
    active_objects = ActiveManager()
    deactivated_objects = DeactivateManager()

    class Meta:
        abstract = True

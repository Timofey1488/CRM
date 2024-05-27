from django.db import models


class UserRole(models.TextChoices):  # User Type
    GUEST = "guest"
    WORKER = "worker"
    OWNER = "owner"


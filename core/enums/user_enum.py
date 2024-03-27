from django.db import models


class UserRole(models.TextChoices):  # User Type
    CLIENT = "client"
    WORKER = "worker"
    OWNER = "owner"


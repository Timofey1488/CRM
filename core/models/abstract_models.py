from django.core.validators import MinValueValidator
from django.db import models


class Base(models.Model):  # Model with common fields
    is_active = models.BooleanField(default=True)
    update_time = models.DateTimeField(auto_now=True)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True



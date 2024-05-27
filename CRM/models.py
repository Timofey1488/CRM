from datetime import datetime

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from core.enums.order_state import OrderState
from core.enums.user_enum import UserRole
from core.models.abstract_models import Base


class User(AbstractUser):
    # Define the role
    role = models.CharField(max_length=50, choices=UserRole.choices, default=UserRole.GUEST)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)


class Client(Base):
    phone = models.CharField(max_length=256, verbose_name="Phone Number")
    full_name = models.CharField(max_length=256, verbose_name='Full name')
    notes = models.CharField(max_length=256, verbose_name="Client Notes", null=True)

    def __str__(self):
        return self.full_name + '' + self.phone

    class Meta:
        # Уникальный индекс для комбинации first_name, last_name и phone
        unique_together = [['full_name', 'phone']]


class Worker(Base):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, verbose_name="Phone Number", unique=True)
    position = models.CharField(max_length=30, verbose_name='Position')
    hire_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.user.first_name + self.phone


class Order(Base):
    date_accept = models.DateField(null=True, blank=True)
    date_ready = models.DateTimeField(null=True, blank=True)
    service_name = models.CharField(max_length=256, verbose_name="Service Name")
    notes = models.CharField(max_length=256, verbose_name="Notes", null=True, blank=True)
    total_sum = models.DecimalField(validators=[MinValueValidator(0.00)],
                                    default=0,
                                    decimal_places=2,
                                    max_digits=9
                                    )
    state = models.CharField(max_length=21,
                             choices=[(state.value, state.name) for state in OrderState],
                             default=OrderState.PLANNED.value
                             )
    client = models.ForeignKey('Client', on_delete=models.CASCADE)
    is_urgent = models.BooleanField(default=False, null=True, blank=True)
    is_notified = models.BooleanField(default=False)
    worker = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')

    def __str__(self):
        return str(self.date_accept) + " " + str(self.service_name) + str(self.total_sum) + 'руб'

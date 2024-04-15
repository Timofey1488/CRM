from datetime import datetime

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from core.enums.order_state import OrderState
from core.enums.user_enum import UserRole
from core.models.abstract_models import Base, BaseStatistics


class User(AbstractUser):
    # Define the role
    role = models.CharField(max_length=50, choices=UserRole.choices, default=UserRole.CLIENT)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)


class Client(Base):
    phone = models.CharField(max_length=15, verbose_name="Phone Number")
    full_name = models.CharField(max_length=256, verbose_name='Full name')

    def __str__(self):
        return self.full_name + self.phone

    class Meta:
        # Уникальный индекс для комбинации first_name, last_name и phone
        unique_together = [['full_name', 'phone']]


class ClientStatistics(Base):
    client = models.OneToOneField(Client, on_delete=models.CASCADE)

    total_orders = models.DecimalField(validators=[MinValueValidator(0.00)],
                                       default=0,
                                       decimal_places=2,
                                       max_digits=9)
    total_sum_paid = models.DecimalField(validators=[MinValueValidator(0.00)],
                                         default=0,
                                         decimal_places=2,
                                         max_digits=9)


class Worker(Base):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, verbose_name="Phone Number", unique=True)
    position = models.CharField(max_length=30, verbose_name='Position')

    def __str__(self):
        return self.user.first_name + self.phone


class WorkerHistory(Base):
    worker = models.OneToOneField(Worker, on_delete=models.CASCADE)

    date = models.DateTimeField()
    cost = models.DecimalField(decimal_places=2,
                               max_digits=9)

    order = models.ForeignKey('Order', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.date) + self.worker.user.first_name + self.worker.user.last_name


class WorkerStatistics(BaseStatistics):
    worker = models.OneToOneField(Worker, on_delete=models.CASCADE)

    total_completed_orders = models.DecimalField(validators=[MinValueValidator(0.00)],
                                                 default=0,
                                                 decimal_places=2,
                                                 max_digits=9
                                                 )


class Owner(Base):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, verbose_name="Phone Number", unique=True)
    address = models.CharField(max_length=256, verbose_name="Home address")

    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.first_name + self.phone


class Order(Base):
    date_ready = models.DateTimeField(default=datetime.now)
    service_name = models.CharField(max_length=256, verbose_name="Service Name")
    order_description = models.CharField(max_length=256, verbose_name="Order Description")
    notes = models.CharField(max_length=256, verbose_name="Notes")
    total_sum = models.DecimalField(validators=[MinValueValidator(0.00)],
                                    default=0,
                                    decimal_places=2,
                                    max_digits=9
                                    )
    state = models.CharField(max_length=20,
                             choices=[(state.value, state.name) for state in OrderState],
                             default=OrderState.PLANNED.value
                             )
    client = models.ForeignKey('Client', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.date_accepted) + str(self.client.full_name)




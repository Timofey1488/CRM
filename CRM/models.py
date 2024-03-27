import datetime

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
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, verbose_name="Phone Number")

    order = models.ForeignKey('Order', on_delete=models.CASCADE)

    def __str__(self):
        return self.user.first_name + self.phone


class ClientStatistics(Base):
    client = models.OneToOneField(Client, on_delete=models.CASCADE)

    total_orders = models.DecimalField(validators=[MinValueValidator(0.00)], default=0)
    total_sum_paid = models.DecimalField(validators=[MinValueValidator(0.00)], default=0)


class Worker(Base):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, verbose_name="Phone Number", unique=True)
    position = models.CharField(max_length=30, verbose_name='Position')

    def __str__(self):
        return self.user.first_name + self.phone


class WorkerHistory(Base):
    worker = models.OneToOneField(Worker, on_delete=models.CASCADE)

    date = models.DateTimeField()
    cost = models.DecimalField()

    order = models.ForeignKey('Order', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.date) + self.worker.user.first_name + self.worker.user.last_name


class WorkerStatistics(BaseStatistics):
    worker = models.OneToOneField(Worker, on_delete=models.CASCADE)

    total_completed_orders = models.DecimalField(validators=[MinValueValidator(0.00)], default=0)


class Owner(Base):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, verbose_name="Phone Number", unique=True)
    address = models.CharField(max_length=256, verbose_name="Home address")

    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.first_name + self.phone


class Order(Base):
    create_time = models.DateTimeField()
    details = models.CharField(max_length=256, verbose_name="Notes")
    total_sum = models.DecimalField(validators=[MinValueValidator(0.00)], default=0)
    state = models.CharField(max_length=10,
                             choices=[(state.value, state.name) for state in OrderState],
                             default=OrderState.NONE.value
                             )

    def __str__(self):
        return str(self.create_time) + str(self.total_sum)


# IN PROCESS(NEED TO CHECK)

class OrderService(Base):
    quantity = models.IntegerField(default=1)

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    service = models.ForeignKey('Service', on_delete=models.CASCADE)

    def __str__(self):
        return f"Order: {self.order}, Service: {self.service}"


class Service(Base):
    service_name = models.CharField(max_length=100, verbose_name="Service name")
    price = models.DecimalField(validators=[MinValueValidator(0.00)], default=0)

    def __str__(self):
        return str(self.create_time) + str(self.total_sum)


class CategoryService(Base):
    category_name = models.CharField(max_length=256, verbose_name="Category name")

    service = models.ForeignKey(Service, on_delete=models.CASCADE)

    def __str__(self):
        return self.category_name

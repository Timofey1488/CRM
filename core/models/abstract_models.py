from django.core.validators import MinValueValidator
from django.db import models


class Base(models.Model):  # Model with common fields
    is_active = models.BooleanField(default=True)
    update_time = models.DateTimeField(auto_now=True)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class BaseStatistics(models.Model):  # Model with common fields
    total_for_all_time = models.DecimalField(max_digits=10,
                                             decimal_places=2,
                                             validators=[MinValueValidator(0.00)],
                                             default=0.0)
    total_earn_for_month = models.DecimalField(max_digits=10,
                                               decimal_places=2,
                                               validators=[MinValueValidator(0.00)],
                                               default=0.0)
    total_earn_for_week = models.DecimalField(max_digits=10,
                                              decimal_places=2,
                                              validators=[MinValueValidator(0.00)],
                                              default=0.0)
    total_earn_for_day = models.DecimalField(max_digits=10,
                                             decimal_places=2,
                                             validators=[MinValueValidator(0.00)],
                                             default=0.0)

    class Meta:
        abstract = True

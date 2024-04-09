from django.db import models


class OrderState(models.TextChoices):
    PLANNED = "Запланирован"
    IN_PROGRESS = "В работе"
    COMPLETED = "Сделан"
    COMPLETED_BUT_NOT_PAID = "Сделан, но неоплачен"

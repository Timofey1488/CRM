from django.db import models


class OrderState(models.TextChoices):
    PLANNED = "Запланирован"
    IN_PROGRESS = "В работе"
    COMPLETED = "Сделан"
    PAID = "Оплачен"
    PAID_BUT_NOT_COMPLETED = "Оплачен, но не сделан"
    COMPLETED_BUT_NOT_PAID = "Сделан, но неоплачен"
    TAKEN = "Клиент забрал заказ"

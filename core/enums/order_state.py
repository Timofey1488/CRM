from django.db import models


class OrderState(models.TextChoices):
    NONE = "Ничего"
    READY = "Готово"
    NEED_FITTING = "Нужна примерка"
    IN_PROCESS = "В работе"

# Generated by Django 4.2.11 on 2024-05-10 12:59

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("CRM", "0014_order_is_urgent"),
    ]

    operations = [
        migrations.AddField(
            model_name="worker",
            name="balance",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=9,
                validators=[django.core.validators.MinValueValidator(0.0)],
            ),
        ),
        migrations.AddField(
            model_name="worker",
            name="hire_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]

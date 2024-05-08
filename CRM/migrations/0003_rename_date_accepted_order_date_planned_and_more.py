# Generated by Django 4.2.11 on 2024-04-09 19:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("CRM", "0002_alter_client_unique_together_client_full_name_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="order",
            old_name="date_accepted",
            new_name="date_planned",
        ),
        migrations.AlterField(
            model_name="order",
            name="state",
            field=models.CharField(
                choices=[
                    ("Запланирован", "PLANNED"),
                    ("В работе", "IN_PROGRESS"),
                    ("Сделан", "COMPLETED"),
                    ("Сделан, но неоплачен", "COMPLETED_BUT_NOT_PAID"),
                ],
                default="Запланирован",
                max_length=20,
            ),
        ),
    ]

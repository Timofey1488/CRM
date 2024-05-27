# Generated by Django 4.2.11 on 2024-05-17 20:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("CRM", "0019_order_is_notified"),
    ]

    operations = [
        migrations.CreateModel(
            name="BusinessAnalytics",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateField()),
                ("total_orders", models.IntegerField()),
                ("total_revenue", models.DecimalField(decimal_places=2, max_digits=12)),
                (
                    "average_order_value",
                    models.DecimalField(decimal_places=2, max_digits=12),
                ),
                ("total_urgent_orders", models.IntegerField()),
            ],
            options={
                "verbose_name_plural": "Business Analytics",
                "unique_together": {("date",)},
            },
        ),
        migrations.RemoveField(
            model_name="workerhistory",
            name="order",
        ),
        migrations.RemoveField(
            model_name="workerhistory",
            name="worker",
        ),
        migrations.DeleteModel(
            name="ClientStatistics",
        ),
        migrations.DeleteModel(
            name="WorkerHistory",
        ),
    ]

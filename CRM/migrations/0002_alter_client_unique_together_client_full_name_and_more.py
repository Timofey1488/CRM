# Generated by Django 4.2.11 on 2024-03-29 16:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("CRM", "0001_initial"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="client",
            unique_together=set(),
        ),
        migrations.AddField(
            model_name="client",
            name="full_name",
            field=models.CharField(default=2, max_length=256, verbose_name="Full name"),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name="client",
            unique_together={("full_name", "phone")},
        ),
        migrations.RemoveField(
            model_name="client",
            name="user",
        ),
    ]

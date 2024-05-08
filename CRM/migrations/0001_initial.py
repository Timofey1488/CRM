# Generated by Django 4.2.11 on 2024-03-29 15:44

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="Client",
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
                ("is_active", models.BooleanField(default=True)),
                ("update_time", models.DateTimeField(auto_now=True)),
                ("create_time", models.DateTimeField(auto_now_add=True)),
                ("phone", models.CharField(max_length=15, verbose_name="Phone Number")),
            ],
        ),
        migrations.CreateModel(
            name="Order",
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
                ("is_active", models.BooleanField(default=True)),
                ("update_time", models.DateTimeField(auto_now=True)),
                ("create_time", models.DateTimeField(auto_now_add=True)),
                ("date_accepted", models.DateTimeField()),
                ("date_ready", models.DateTimeField()),
                (
                    "service_name",
                    models.CharField(max_length=256, verbose_name="Service Name"),
                ),
                (
                    "order_description",
                    models.CharField(max_length=256, verbose_name="Order Description"),
                ),
                ("notes", models.CharField(max_length=256, verbose_name="Notes")),
                (
                    "total_sum",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=9,
                        validators=[django.core.validators.MinValueValidator(0.0)],
                    ),
                ),
                (
                    "state",
                    models.CharField(
                        choices=[
                            ("Ничего", "NONE"),
                            ("Готово", "READY"),
                            ("Нужна примерка", "NEED_FITTING"),
                            ("В работе", "IN_PROCESS"),
                        ],
                        default="Ничего",
                        max_length=14,
                    ),
                ),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="CRM.client"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Worker",
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
                ("is_active", models.BooleanField(default=True)),
                ("update_time", models.DateTimeField(auto_now=True)),
                ("create_time", models.DateTimeField(auto_now_add=True)),
                (
                    "phone",
                    models.CharField(
                        max_length=15, unique=True, verbose_name="Phone Number"
                    ),
                ),
                ("position", models.CharField(max_length=30, verbose_name="Position")),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="User",
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
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        error_messages={
                            "unique": "A user with that username already exists."
                        },
                        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
                        max_length=150,
                        unique=True,
                        validators=[
                            django.contrib.auth.validators.UnicodeUsernameValidator()
                        ],
                        verbose_name="username",
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        blank=True, max_length=254, verbose_name="email address"
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date joined"
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("client", "Client"),
                            ("worker", "Worker"),
                            ("owner", "Owner"),
                        ],
                        default="client",
                        max_length=50,
                    ),
                ),
                ("first_name", models.CharField(max_length=50)),
                ("last_name", models.CharField(max_length=50)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
                "abstract": False,
            },
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="WorkerStatistics",
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
                (
                    "total_for_all_time",
                    models.DecimalField(
                        decimal_places=2,
                        default=0.0,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0.0)],
                    ),
                ),
                (
                    "total_earn_for_month",
                    models.DecimalField(
                        decimal_places=2,
                        default=0.0,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0.0)],
                    ),
                ),
                (
                    "total_earn_for_week",
                    models.DecimalField(
                        decimal_places=2,
                        default=0.0,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0.0)],
                    ),
                ),
                (
                    "total_earn_for_day",
                    models.DecimalField(
                        decimal_places=2,
                        default=0.0,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0.0)],
                    ),
                ),
                (
                    "total_completed_orders",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=9,
                        validators=[django.core.validators.MinValueValidator(0.0)],
                    ),
                ),
                (
                    "worker",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, to="CRM.worker"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="WorkerHistory",
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
                ("is_active", models.BooleanField(default=True)),
                ("update_time", models.DateTimeField(auto_now=True)),
                ("create_time", models.DateTimeField(auto_now_add=True)),
                ("date", models.DateTimeField()),
                ("cost", models.DecimalField(decimal_places=2, max_digits=9)),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="CRM.order"
                    ),
                ),
                (
                    "worker",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, to="CRM.worker"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="worker",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.CreateModel(
            name="Owner",
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
                ("is_active", models.BooleanField(default=True)),
                ("update_time", models.DateTimeField(auto_now=True)),
                ("create_time", models.DateTimeField(auto_now_add=True)),
                (
                    "phone",
                    models.CharField(
                        max_length=15, unique=True, verbose_name="Phone Number"
                    ),
                ),
                (
                    "address",
                    models.CharField(max_length=256, verbose_name="Home address"),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "worker",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="CRM.worker"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ClientStatistics",
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
                ("is_active", models.BooleanField(default=True)),
                ("update_time", models.DateTimeField(auto_now=True)),
                ("create_time", models.DateTimeField(auto_now_add=True)),
                (
                    "total_orders",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=9,
                        validators=[django.core.validators.MinValueValidator(0.0)],
                    ),
                ),
                (
                    "total_sum_paid",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=9,
                        validators=[django.core.validators.MinValueValidator(0.0)],
                    ),
                ),
                (
                    "client",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, to="CRM.client"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="client",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AlterUniqueTogether(
            name="client",
            unique_together={("user", "phone")},
        ),
    ]

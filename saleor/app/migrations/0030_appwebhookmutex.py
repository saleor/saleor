# Generated by Django 4.2.18 on 2025-04-03 15:47

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0029_alter_app_identifier"),
    ]

    operations = [
        migrations.CreateModel(
            name="AppWebhookMutex",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("acquired_at", models.DateTimeField(null=True)),
                ("uuid", models.UUIDField(default=uuid.uuid4, unique=True)),
                (
                    "app",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="webhook_mutexes",
                        to="app.app",
                        verbose_name="App",
                    ),
                ),
            ],
        ),
    ]

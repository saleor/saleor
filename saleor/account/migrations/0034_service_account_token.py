import django.db.models.deletion
import oauthlib.common
from django.db import migrations, models


def move_existing_token(apps, schema_editor):
    ServiceAccount = apps.get_model("account", "ServiceAccount")
    for service_account in ServiceAccount.objects.iterator():
        service_account.tokens.create(
            name="Default", auth_token=service_account.auth_token
        )


class Migration(migrations.Migration):
    dependencies = [("account", "0033_serviceaccount")]

    operations = [
        migrations.CreateModel(
            name="ServiceAccountToken",
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
                ("name", models.CharField(blank=True, default="", max_length=128)),
                (
                    "auth_token",
                    models.CharField(
                        default=oauthlib.common.generate_token,
                        max_length=30,
                        unique=True,
                    ),
                ),
                (
                    "service_account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tokens",
                        to="account.ServiceAccount",
                    ),
                ),
            ],
        ),
        migrations.RunPython(move_existing_token),
        migrations.RemoveField(model_name="serviceaccount", name="auth_token"),
    ]

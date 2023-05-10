# Generated by Django 3.2.19 on 2023-05-08 09:36

from django.db import migrations, models
from ...settings import get_bool_from_env

qwe = get_bool_from_env("ENABLE_ACCOUNT_CONFIRMATION_BY_EMAIL", True)


def set_enable_account_confirmation_by_email_flag(apps, schema_editor):
    confirmation_flag = get_bool_from_env("ENABLE_ACCOUNT_CONFIRMATION_BY_EMAIL", True)
    SiteSettings = apps.get_model("site", "SiteSettings")
    SiteSettings.objects.update(enable_account_confirmation_by_email=confirmation_flag)


class Migration(migrations.Migration):
    dependencies = [
        ("site", "0036_remove_order_settings"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="enable_account_confirmation_by_email",
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(
            set_enable_account_confirmation_by_email_flag,
            migrations.RunPython.noop,
        ),
    ]

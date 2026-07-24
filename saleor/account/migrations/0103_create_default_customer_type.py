from django.db import migrations


def create_default_customer_type(apps, _schema_editor):
    CustomerType = apps.get_model("account", "CustomerType")
    CustomerType.objects.get_or_create(
        is_default=True,
        defaults={"name": "Default", "slug": "default"},
    )


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0102_user_user_customer_type_idx"),
    ]
    operations = [
        migrations.RunPython(create_default_customer_type, migrations.RunPython.noop)
    ]

import uuid

from django.db import migrations, models


def get_token():
    return str(uuid.uuid4())


def create_uuid(apps, schema_editor):
    accounts = apps.get_model("account", "User").objects.all()
    for account in accounts:
        account.token = get_token()
        account.save()


class Migration(migrations.Migration):

    dependencies = [("account", "0020_user_token")]

    operations = [
        migrations.RunPython(create_uuid),
        migrations.AlterField(
            model_name="user",
            name="token",
            field=models.UUIDField(default=get_token, editable=False, unique=True),
        ),
    ]

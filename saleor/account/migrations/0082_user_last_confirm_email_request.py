from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0081_update_user_is_confirmed"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="last_confirm_email_request",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

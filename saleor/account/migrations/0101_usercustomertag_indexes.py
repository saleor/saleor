from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("account", "0100_customertag_usercustomertag"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="usercustomertag",
            index=models.Index(fields=["user"], name="user_customer_tag_user_idx"),
        ),
        AddIndexConcurrently(
            model_name="usercustomertag",
            index=models.Index(fields=["tag"], name="user_customer_tag_tag_idx"),
        ),
    ]

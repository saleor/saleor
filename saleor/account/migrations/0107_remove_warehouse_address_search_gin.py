from django.contrib.postgres.operations import RemoveIndexConcurrently
from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("account", "0106_drop_idx_user_full_name"),
    ]

    operations = [
        RemoveIndexConcurrently(
            model_name="address",
            name="warehouse_address_search_gin",
        ),
    ]

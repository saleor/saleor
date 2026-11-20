from django.contrib.postgres.operations import RemoveIndexConcurrently
from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("order", "0228_add_order_base_prices"),
    ]

    operations = [
        RemoveIndexConcurrently(
            model_name="order",
            name="order_search_gin",
        ),
    ]

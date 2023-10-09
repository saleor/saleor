from django.db import migrations
from django.apps import apps as registry
from django.db.models.signals import post_migrate

from .tasks.saleor3_17 import recalculate_undiscounted_prices
from django.db.models import Q, F


def recalculate_undiscounted_prices_for_order(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        recalculate_undiscounted_prices.delay()

    # Make sure that there are OrderLines that needs to be updated
    # to prevent running unneeded task
    OrderLine = apps.get_model("order", "OrderLine")
    if not OrderLine.objects.filter(
        (
            Q(
                undiscounted_unit_price_net_amount=F(
                    "undiscounted_unit_price_gross_amount"
                )
            )
            | Q(
                undiscounted_total_price_net_amount=F(
                    "undiscounted_total_price_gross_amount"
                )
            )
        )
        & Q(tax_rate__gt=0)
    ):
        #exist dodac
        return

    sender = registry.get_app_config("order")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0174_order_idx_order_created_at"),
    ]

    operations = [
        migrations.RunPython(
            recalculate_undiscounted_prices_for_order,
            reverse_code=migrations.RunPython.noop,
        ),
    ]

from django.db import migrations, models
from django.db.models import F


def calculate_undiscounted_total_values(apps, *_args, **_kwargs):
    Order = apps.get_model("order", "Order")
    Order.objects.update(
        undiscounted_total_gross_amount=F("total_gross_amount") + F("discount_amount")
    )
    Order.objects.update(
        undiscounted_total_net_amount=F("total_net_amount") + F("discount_amount")
    )


def create_order_discount_relations(apps, *_args, **_kwargs):
    Order = apps.get_model("order", "Order")
    orders_with_discount = Order.objects.exclude(discount_amount=0.0)
    for order in orders_with_discount.iterator():
        order.discounts.create(
            value_type="fixed",
            value=order.discount_amount,
            amount_value=order.discount_amount,
            name=order.discount_name,
            type="voucher",
            translated_name=order.translated_discount_name,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0097_auto_20210107_1148"),
        ("discount", "0024_orderdiscount"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="undiscounted_total_gross_amount",
            field=models.DecimalField(decimal_places=3, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name="order",
            name="undiscounted_total_net_amount",
            field=models.DecimalField(decimal_places=3, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name="orderline",
            name="unit_discount_amount",
            field=models.DecimalField(decimal_places=3, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name="orderline",
            name="unit_discount_value",
            field=models.DecimalField(decimal_places=3, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name="orderline",
            name="unit_discount_reason",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="orderline",
            name="unit_discount_type",
            field=models.CharField(
                choices=[("fixed", "fixed"), ("percentage", "%")],
                default="fixed",
                max_length=10,
            ),
        ),
        migrations.RunPython(calculate_undiscounted_total_values),
        migrations.RunPython(create_order_discount_relations),
    ]

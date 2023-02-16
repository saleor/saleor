from django.db import migrations


def set_origin_and_original_order_values(apps, schema_editor):
    Order = apps.get_model("order", "Order")
    draft_events = ["placed_from_draft", "draft_created"]
    Order.objects.filter(events__type__in=draft_events).update(origin="draft")
    orders = []
    for order in Order.objects.filter(
        events__type="draft_created_from_replace"
    ).iterator():
        order.origin = "reissue"
        order.original_id = order.events.get(
            type="draft_created_from_replace"
        ).parameters.get("related_order_pk")
        orders.append(order)
    Order.objects.bulk_update(orders, ["origin", "original"])
    Order.objects.exclude(
        events__type__in=draft_events + ["draft_created_from_replace"]
    ).update(origin="checkout")


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0106_origin_and_original"),
    ]

    operations = [
        migrations.RunPython(
            set_origin_and_original_order_values, migrations.RunPython.noop
        )
    ]

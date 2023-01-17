from datetime import timedelta
from unittest.mock import ANY, patch

import graphene
from django.utils import timezone
from freezegun import freeze_time

from ..models import Sale
from ..tasks import fetch_catalogue_infos, send_sale_toggle_notifications


def test_fetch_catalogue_infos(sale, new_sale):
    # given
    sales = Sale.objects.all()

    # when
    catalogue_infos = fetch_catalogue_infos(sales)

    # then
    for sale_instance in sales:
        catalogue_info = catalogue_infos[sale_instance.id]
        assert catalogue_info["categories"] == set(
            graphene.Node.to_global_id("Category", id)
            for id in sale_instance.categories.all().values_list("id", flat=True)
        )
        assert catalogue_info["collections"] == set(
            graphene.Node.to_global_id("Collection", id)
            for id in sale_instance.collections.all().values_list("id", flat=True)
        )
        assert catalogue_info["products"] == set(
            graphene.Node.to_global_id("Product", id)
            for id in sale_instance.products.all().values_list("id", flat=True)
        )
        assert catalogue_info["variants"] == set(
            graphene.Node.to_global_id("ProductVariant", id)
            for id in sale_instance.variants.all().values_list("id", flat=True)
        )


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.plugins.manager.PluginsManager.sale_toggle")
def test_send_sale_toggle_notifications(sale_toggle_mock):
    # given
    now = timezone.now()
    sales = Sale.objects.bulk_create([Sale(name=f"Sale-{i}") for i in range(10)])

    # sales with start date before current date
    # without notification sent day - should be sent
    sales[0].start_date = now - timedelta(days=1)
    sales[0].notification_sent_datetime = None

    # with notification sent day after the start date - shouldn't be sent
    sales[1].start_date = now - timedelta(days=1)
    sales[1].notification_sent_datetime = now - timedelta(minutes=2)

    # with notification sent day before the start date - should be sent
    sales[2].start_date = now - timedelta(minutes=2)
    sales[2].notification_sent_datetime = now - timedelta(minutes=5)

    # sales with start date after current date - shouldn't be sent
    # without notification sent day
    sales[3].start_date = now + timedelta(days=1)
    sales[3].notification_sent_datetime = None

    # with notification sent day before the start date
    sales[4].start_date = now + timedelta(days=1)
    sales[4].notification_sent_datetime = now - timedelta(minutes=5)

    # sales with end date before current date
    # without notification sent day - should be sent
    sales[5].end_date = now - timedelta(days=1)
    sales[5].notification_sent_datetime = None

    # with notification sent day after the start date - shouldn't be sent
    sales[6].start_date = now - timedelta(days=2)
    sales[6].end_date = now - timedelta(days=1)
    sales[6].notification_sent_datetime = now - timedelta(minutes=2)

    # with notification sent day before the start date - should be sent
    sales[7].start_date = now - timedelta(days=2)
    sales[7].end_date = now - timedelta(minutes=2)
    sales[7].notification_sent_datetime = now - timedelta(minutes=5)

    # sales with end date after current date
    # without notification sent day
    sales[8].start_date = now + timedelta(days=2)
    sales[8].end_date = now + timedelta(days=1)
    sales[8].notification_sent_datetime = None

    # with notification sent day before the start date
    sales[9].start_date = now + timedelta(days=2)
    sales[9].end_date = now + timedelta(days=1)
    sales[9].notification_sent_datetime = now - timedelta(minutes=5)

    Sale.objects.bulk_update(
        sales,
        [
            "start_date",
            "end_date",
            "notification_sent_datetime",
        ],
    )

    # when
    send_sale_toggle_notifications()

    # then
    assert sale_toggle_mock.call_count == 4

    started_args_list = [args.args for args in sale_toggle_mock.call_args_list]
    assert (sales[0], ANY) in started_args_list
    assert (sales[2], ANY) in started_args_list
    assert (sales[5], ANY) in started_args_list
    assert (sales[7], ANY) in started_args_list

    for index in [0, 2, 5, 7]:
        sales[index].refresh_from_db()
        assert sales[index].notification_sent_datetime == now

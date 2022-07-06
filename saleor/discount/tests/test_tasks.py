from datetime import timedelta
from unittest.mock import ANY, patch

from django.utils import timezone

from ..models import Sale
from ..tasks import (
    fetch_catalogue_infos,
    send_sale_started_and_sale_ended_notifications,
)


def test_fetch_catalogue_infos(sale, new_sale):
    # given
    sales = Sale.objects.all()

    # when
    catalogue_infos = fetch_catalogue_infos(sales)

    # then
    for sale_instance in sales:
        catalogue_info = catalogue_infos[sale_instance.id]
        assert catalogue_info["categories"] == set(
            sale_instance.categories.all().values_list("id", flat=True)
        )
        assert catalogue_info["collections"] == set(
            sale_instance.collections.all().values_list("id", flat=True)
        )
        assert catalogue_info["products"] == set(
            sale_instance.products.all().values_list("id", flat=True)
        )
        assert catalogue_info["variants"] == set(
            sale_instance.variants.all().values_list("id", flat=True)
        )


@patch("saleor.plugins.manager.PluginsManager.sale_ended")
@patch("saleor.plugins.manager.PluginsManager.sale_started")
def test_send_sale_started_and_sale_ended_notifications(
    sale_started_mock, sale_ended_mock
):
    # given
    now = timezone.now()
    sales = Sale.objects.bulk_create([Sale(name=f"Sale-{i}") for i in range(10)])

    # sales with start date before current date
    for sale in sales[:2]:
        sale.start_date = now - timedelta(days=1)
        sale.started_notification_sent = False
        sale.ended_notification_sent = True

    sales[2].start_date = now - timedelta(days=1)
    sales[2].started_notification_sent = True
    sales[2].ended_notification_sent = True

    # sales with start date after current date
    for sale in sales[3:5]:
        sale.start_date = now + timedelta(days=1)
        sale.started_notification_sent = False
        sale.ended_notification_sent = True

    # sales with end date before current date
    for sale in sales[5:7]:
        sale.end_date = now - timedelta(days=1)
        sale.ended_notification_sent = False
        sale.started_notification_sent = True

    sales[7].end_date = now - timedelta(days=1)
    sales[7].ended_notification_sent = True
    sales[7].started_notification_sent = True

    # sales with end date after current date
    for sale in sales[8:]:
        sale.end_date = now + timedelta(days=1)
        sale.ended_notification_sent = False
        sale.started_notification_sent = True

    Sale.objects.bulk_update(
        sales,
        [
            "start_date",
            "started_notification_sent",
            "end_date",
            "ended_notification_sent",
        ],
    )

    # when
    send_sale_started_and_sale_ended_notifications()

    # then
    assert sale_started_mock.call_count == 2
    assert sale_ended_mock.call_count == 2

    started_args_list = [args.args for args in sale_started_mock.call_args_list]
    assert (sales[0], ANY) in started_args_list
    assert (sales[1], ANY) in started_args_list

    ended_args_list = [args.args for args in sale_ended_mock.call_args_list]
    assert (sales[5], ANY) in ended_args_list
    assert (sales[6], ANY) in ended_args_list

    sales[0].refresh_from_db()
    sales[1].refresh_from_db()
    assert sales[0].started_notification_sent is True
    assert sales[1].started_notification_sent is True

    sales[5].refresh_from_db()
    sales[6].refresh_from_db()
    assert sales[5].started_notification_sent is True
    assert sales[6].started_notification_sent is True

from collections import defaultdict
from datetime import timedelta
from unittest.mock import ANY, patch

import graphene
from django.utils import timezone
from freezegun import freeze_time

from ..models import Sale
from ..tasks import fetch_catalogue_infos, handle_sale_toggle


def test_fetch_catalogue_infos(sale, new_sale):
    # given
    sales = Sale.objects.all()

    # when
    sale_id_to_catalogue_infos, catalogue_infos = fetch_catalogue_infos(sales)

    # then
    expected_catalogue_info = defaultdict(set)
    for sale_instance in sales:
        catalogue_info = sale_id_to_catalogue_infos[sale_instance.id]
        category_ids = sale_instance.categories.all().values_list("id", flat=True)
        collection_ids = sale_instance.collections.all().values_list("id", flat=True)
        product_ids = sale_instance.products.all().values_list("id", flat=True)
        variant_ids = sale_instance.variants.all().values_list("id", flat=True)
        assert catalogue_info["categories"] == set(
            graphene.Node.to_global_id("Category", id) for id in category_ids
        )
        assert catalogue_info["collections"] == set(
            graphene.Node.to_global_id("Collection", id) for id in collection_ids
        )
        assert catalogue_info["products"] == set(
            graphene.Node.to_global_id("Product", id) for id in product_ids
        )
        assert catalogue_info["variants"] == set(
            graphene.Node.to_global_id("ProductVariant", id) for id in variant_ids
        )
        expected_catalogue_info["categories"].update(set(category_ids))
        expected_catalogue_info["collections"].update(set(collection_ids))
        expected_catalogue_info["products"].update(set(product_ids))
        expected_catalogue_info["variants"].update(set(variant_ids))

    assert catalogue_infos == expected_catalogue_info


@freeze_time("2020-03-18 12:00:00")
@patch(
    "saleor.product.tasks.update_products_discounted_prices_of_catalogues_task.delay"
)
@patch("saleor.plugins.manager.PluginsManager.sale_toggle")
def test_handle_sale_toggle(
    sale_toggle_mock,
    mock_update_products_discounted_prices_of_catalogues,
    collection_list,
    product_list,
    category,
):
    # given
    now = timezone.now()
    sales = Sale.objects.bulk_create([Sale(name=f"Sale-{i}") for i in range(10)])

    variant_ids = []
    for collection, product, sale in zip(collection_list, product_list, sales):
        sale.collections.add(collection)
        sale.products.add(product)
        variant = product.variants.first()
        sale.variants.add(variant)
        variant_ids.append(variant.id)

    sales[7].categories.add(category)

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
    indexes_of_toggle_sales = [0, 2, 5, 7]

    # when
    handle_sale_toggle()

    # then
    assert sale_toggle_mock.call_count == 4

    started_args_list = [args.args for args in sale_toggle_mock.call_args_list]
    for index in indexes_of_toggle_sales:
        assert (sales[index], ANY) in started_args_list

    for index in indexes_of_toggle_sales:
        sales[index].refresh_from_db()
        assert sales[index].notification_sent_datetime == now

    mock_update_products_discounted_prices_of_catalogues.assert_called_once()
    args, kwargs = mock_update_products_discounted_prices_of_catalogues.call_args
    # get ids of instances assigned to sales that toggle
    assert set(kwargs["product_ids"]) == {product_list[0].id, product_list[2].id}
    assert set(kwargs["category_ids"]) == {category.id}
    assert set(kwargs["collection_ids"]) == {
        collection_list[0].id,
        collection_list[2].id,
    }
    assert set(kwargs["variant_ids"]) == {variant_ids[0], variant_ids[2]}

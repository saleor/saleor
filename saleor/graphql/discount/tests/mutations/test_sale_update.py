from datetime import timedelta
from unittest.mock import patch

import graphene
from django.utils import timezone
from freezegun import freeze_time

from .....discount import DiscountValueType
from .....discount.utils import fetch_catalogue_info
from ....tests.utils import get_graphql_content
from ...enums import DiscountValueTypeEnum
from ...mutations.utils import convert_catalogue_info_to_global_ids

SALE_UPDATE_MUTATION = """
    mutation  saleUpdate($id: ID!, $input: SaleInput!) {
        saleUpdate(id: $id, input: $input) {
            errors {
                field
                code
                message
            }
            sale {
                name
                type
                startDate
                endDate
            }
        }
    }
"""


@patch(
    "saleor.product.tasks.update_products_discounted_prices_of_catalogues_task.delay"
)
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale(
    updated_webhook_mock,
    update_products_discounted_prices_of_catalogues_task_mock,
    staff_api_client,
    sale,
    permission_manage_discounts,
    product_list,
):
    # given
    query = SALE_UPDATE_MUTATION

    # Set discount value type to 'fixed' and change it in mutation
    sale.type = DiscountValueType.FIXED
    sale.save(update_fields=["type"])
    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    category_pks = set(sale.categories.values_list("id", flat=True))
    collection_pks = set(sale.collections.values_list("id", flat=True))
    product_pks = set(sale.products.values_list("id", flat=True))
    variant_pks = set(sale.variants.values_list("id", flat=True))
    new_product_pks = [product.id for product in product_list]

    new_product_ids = [
        graphene.Node.to_global_id("Product", product_id)
        for product_id in new_product_pks
    ]
    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {
            "type": DiscountValueTypeEnum.PERCENTAGE.name,
            "products": new_product_ids,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    current_catalogue = convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale))

    # then
    content = get_graphql_content(response)
    data = content["data"]["saleUpdate"]["sale"]
    assert data["type"] == DiscountValueType.PERCENTAGE.upper()

    updated_webhook_mock.assert_called_once_with(
        sale, previous_catalogue, current_catalogue
    )
    update_products_discounted_prices_of_catalogues_task_mock.assert_called_once()
    args, kwargs = update_products_discounted_prices_of_catalogues_task_mock.call_args
    assert set(kwargs["category_ids"]) == category_pks
    assert set(kwargs["collection_ids"]) == collection_pks
    assert set(kwargs["product_ids"]) == product_pks.union(new_product_pks)
    assert set(kwargs["variant_ids"]) == variant_pks


@patch(
    "saleor.product.tasks.update_products_discounted_prices_of_catalogues_task.delay"
)
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale_name(
    updated_webhook_mock,
    update_products_discounted_prices_of_catalogues_task_mock,
    staff_api_client,
    sale,
    permission_manage_discounts,
    product_list,
):
    # given
    query = SALE_UPDATE_MUTATION

    new_name = "New name"
    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )

    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {
            "name": new_name,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    current_catalogue = convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale))

    # then
    content = get_graphql_content(response)
    data = content["data"]["saleUpdate"]["sale"]
    assert data["name"] == new_name

    updated_webhook_mock.assert_called_once_with(
        sale, previous_catalogue, current_catalogue
    )
    update_products_discounted_prices_of_catalogues_task_mock.assert_not_called()


@freeze_time("2020-03-18 12:00:00")
@patch(
    "saleor.product.tasks.update_products_discounted_prices_of_catalogues_task.delay"
)
@patch("saleor.plugins.manager.PluginsManager.sale_toggle")
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale_start_date_after_current_date_notification_not_sent(
    updated_webhook_mock,
    sale_toggle_mock,
    update_products_discounted_prices_of_catalogues_task_mock,
    staff_api_client,
    sale,
    permission_manage_discounts,
):
    """Ensure the notification is not sent when the start date is set after the current
    date.
    """
    # given
    query = SALE_UPDATE_MUTATION

    sale.notification_sent_datetime = None
    sale.save(update_fields=["notification_sent_datetime"])

    category_pks = set(sale.categories.values_list("id", flat=True))
    collection_pks = set(sale.collections.values_list("id", flat=True))
    product_pks = set(sale.products.values_list("id", flat=True))
    variant_pks = set(sale.variants.values_list("id", flat=True))

    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    start_date = timezone.now() + timedelta(days=1)

    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {"startDate": start_date},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    current_catalogue = convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale))

    content = get_graphql_content(response)
    data = content["data"]["saleUpdate"]["sale"]

    assert data["startDate"] == start_date.isoformat()

    sale.refresh_from_db()
    assert sale.notification_sent_datetime is None

    updated_webhook_mock.assert_called_once_with(
        sale, previous_catalogue, current_catalogue
    )
    sale_toggle_mock.assert_not_called()
    update_products_discounted_prices_of_catalogues_task_mock.assert_called_once()
    args, kwargs = update_products_discounted_prices_of_catalogues_task_mock.call_args
    assert set(kwargs["category_ids"]) == category_pks
    assert set(kwargs["collection_ids"]) == collection_pks
    assert set(kwargs["product_ids"]) == product_pks
    assert set(kwargs["variant_ids"]) == variant_pks


@freeze_time("2020-03-18 12:00:00")
@patch(
    "saleor.product.tasks.update_products_discounted_prices_of_catalogues_task.delay"
)
@patch("saleor.plugins.manager.PluginsManager.sale_toggle")
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale_start_date_before_current_date_notification_already_sent(
    updated_webhook_mock,
    sale_toggle_mock,
    update_products_discounted_prices_of_catalogues_task_mock,
    staff_api_client,
    sale,
    permission_manage_discounts,
):
    """Ensure the notification is not sent when the start date is set before
    current date and notification was already sent.
    """
    # given
    query = SALE_UPDATE_MUTATION
    now = timezone.now()

    # Set discount value type to 'fixed' and change it in mutation
    sale.type = DiscountValueType.FIXED
    notification_sent_datetime = now - timedelta(minutes=5)
    sale.notification_sent_datetime = notification_sent_datetime
    sale.save(update_fields=["type", "notification_sent_datetime"])

    category_pks = set(sale.categories.values_list("id", flat=True))
    collection_pks = set(sale.collections.values_list("id", flat=True))
    product_pks = set(sale.products.values_list("id", flat=True))
    variant_pks = set(sale.variants.values_list("id", flat=True))

    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    start_date = timezone.now() - timedelta(days=1)
    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {"startDate": start_date},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    current_catalogue = convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale))

    # then
    content = get_graphql_content(response)
    data = content["data"]["saleUpdate"]["sale"]
    assert data["startDate"] == start_date.isoformat()

    sale.refresh_from_db()
    assert sale.notification_sent_datetime == notification_sent_datetime

    updated_webhook_mock.assert_called_once_with(
        sale, previous_catalogue, current_catalogue
    )
    sale_toggle_mock.assert_not_called()
    update_products_discounted_prices_of_catalogues_task_mock.assert_called_once()
    args, kwargs = update_products_discounted_prices_of_catalogues_task_mock.call_args
    assert set(kwargs["category_ids"]) == category_pks
    assert set(kwargs["collection_ids"]) == collection_pks
    assert set(kwargs["product_ids"]) == product_pks
    assert set(kwargs["variant_ids"]) == variant_pks


@freeze_time("2020-03-18 12:00:00")
@patch(
    "saleor.product.tasks.update_products_discounted_prices_of_catalogues_task.delay"
)
@patch("saleor.plugins.manager.PluginsManager.sale_toggle")
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale_start_date_before_current_date_notification_sent(
    updated_webhook_mock,
    sale_toggle_mock,
    update_products_discounted_prices_of_catalogues_task_mock,
    staff_api_client,
    sale,
    permission_manage_discounts,
):
    """Ensure the sale_toggle notification is sent and the notification date is set
    when the start date is set before current date and the notification hasn't been sent
    before.
    """

    query = SALE_UPDATE_MUTATION

    # Set discount value type to 'fixed' and change it in mutation
    sale.type = DiscountValueType.FIXED
    sale.notification_sent_datetime = None
    sale.save(update_fields=["type", "notification_sent_datetime"])

    category_pks = set(sale.categories.values_list("id", flat=True))
    collection_pks = set(sale.collections.values_list("id", flat=True))
    product_pks = set(sale.products.values_list("id", flat=True))
    variant_pks = set(sale.variants.values_list("id", flat=True))

    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    start_date = timezone.now() - timedelta(days=1)

    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {"startDate": start_date},
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    current_catalogue = convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale))

    content = get_graphql_content(response)
    data = content["data"]["saleUpdate"]["sale"]
    assert data["startDate"] == start_date.isoformat()

    sale.refresh_from_db()
    assert sale.notification_sent_datetime == timezone.now()

    updated_webhook_mock.assert_called_once_with(
        sale, previous_catalogue, current_catalogue
    )
    sale_toggle_mock.assert_called_once_with(sale, current_catalogue)
    update_products_discounted_prices_of_catalogues_task_mock.assert_called_once()
    args, kwargs = update_products_discounted_prices_of_catalogues_task_mock.call_args
    assert set(kwargs["category_ids"]) == category_pks
    assert set(kwargs["collection_ids"]) == collection_pks
    assert set(kwargs["product_ids"]) == product_pks
    assert set(kwargs["variant_ids"]) == variant_pks


@freeze_time("2020-03-18 12:00:00")
@patch(
    "saleor.product.tasks.update_products_discounted_prices_of_catalogues_task.delay"
)
@patch("saleor.plugins.manager.PluginsManager.sale_toggle")
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale_end_date_after_current_date_notification_not_sent(
    updated_webhook_mock,
    sale_toggle_mock,
    update_products_discounted_prices_of_catalogues_task_mock,
    staff_api_client,
    sale,
    permission_manage_discounts,
):
    """Ensure the notification is not sent when the end date is set after
    the current date.
    """
    # given
    query = SALE_UPDATE_MUTATION

    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    end_date = timezone.now() + timedelta(days=1)

    category_pks = set(sale.categories.values_list("id", flat=True))
    collection_pks = set(sale.collections.values_list("id", flat=True))
    product_pks = set(sale.products.values_list("id", flat=True))
    variant_pks = set(sale.variants.values_list("id", flat=True))

    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {"endDate": end_date},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    current_catalogue = convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale))

    content = get_graphql_content(response)
    data = content["data"]["saleUpdate"]["sale"]

    assert data["endDate"] == end_date.isoformat()

    sale.refresh_from_db()
    assert sale.notification_sent_datetime is None

    updated_webhook_mock.assert_called_once_with(
        sale, previous_catalogue, current_catalogue
    )
    sale_toggle_mock.assert_not_called()
    update_products_discounted_prices_of_catalogues_task_mock.assert_called_once()
    args, kwargs = update_products_discounted_prices_of_catalogues_task_mock.call_args
    assert set(kwargs["category_ids"]) == category_pks
    assert set(kwargs["collection_ids"]) == collection_pks
    assert set(kwargs["product_ids"]) == product_pks
    assert set(kwargs["variant_ids"]) == variant_pks


@freeze_time("2020-03-18 12:00:00")
@patch(
    "saleor.product.tasks.update_products_discounted_prices_of_catalogues_task.delay"
)
@patch("saleor.plugins.manager.PluginsManager.sale_toggle")
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale_end_date_before_current_date_notification_already_sent(
    updated_webhook_mock,
    sale_toggle_mock,
    update_products_discounted_prices_of_catalogues_task_mock,
    staff_api_client,
    sale,
    permission_manage_discounts,
):
    """Ensure the notification is sent when the end date is set before
    current date, the notification was already sent but the end date was not set before.
    It means we need to notify about ending the sale.
    """
    # given
    query = SALE_UPDATE_MUTATION

    now = timezone.now()

    # Set discount value type to 'fixed' and change it in mutation
    sale.type = DiscountValueType.FIXED
    notification_sent_datetime = now - timedelta(minutes=5)
    sale.notification_sent_datetime = notification_sent_datetime
    sale.save(update_fields=["type", "notification_sent_datetime"])

    category_pks = set(sale.categories.values_list("id", flat=True))
    collection_pks = set(sale.collections.values_list("id", flat=True))
    product_pks = set(sale.products.values_list("id", flat=True))
    variant_pks = set(sale.variants.values_list("id", flat=True))

    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    end_date = now - timedelta(days=1)
    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {"endDate": end_date},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    current_catalogue = convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale))

    # then
    content = get_graphql_content(response)
    data = content["data"]["saleUpdate"]["sale"]
    assert data["endDate"] == end_date.isoformat()

    sale.refresh_from_db()
    assert sale.notification_sent_datetime == now

    updated_webhook_mock.assert_called_once_with(
        sale, previous_catalogue, current_catalogue
    )
    sale_toggle_mock.assert_called_once_with(sale, current_catalogue)
    update_products_discounted_prices_of_catalogues_task_mock.assert_called_once()
    args, kwargs = update_products_discounted_prices_of_catalogues_task_mock.call_args
    assert set(kwargs["category_ids"]) == category_pks
    assert set(kwargs["collection_ids"]) == collection_pks
    assert set(kwargs["product_ids"]) == product_pks
    assert set(kwargs["variant_ids"]) == variant_pks


@freeze_time("2020-03-18 12:00:00")
@patch(
    "saleor.product.tasks.update_products_discounted_prices_of_catalogues_task.delay"
)
@patch("saleor.plugins.manager.PluginsManager.sale_toggle")
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale_end_date_before_current_date_notification_sent(
    updated_webhook_mock,
    sale_toggle_mock,
    update_products_discounted_prices_of_catalogues_task_mock,
    staff_api_client,
    sale,
    permission_manage_discounts,
):
    """Ensure the sale_toggle notification is sent and the notification date is set
    when the end date is set before current date and the notification hasn't been sent
    before.
    """

    query = SALE_UPDATE_MUTATION

    # Set discount value type to 'fixed' and change it in mutation
    sale.type = DiscountValueType.FIXED
    sale.notification_sent_datetime = None
    sale.save(update_fields=["type", "notification_sent_datetime"])

    category_pks = set(sale.categories.values_list("id", flat=True))
    collection_pks = set(sale.collections.values_list("id", flat=True))
    product_pks = set(sale.products.values_list("id", flat=True))
    variant_pks = set(sale.variants.values_list("id", flat=True))

    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    end_date = timezone.now() - timedelta(days=1)

    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {"endDate": end_date},
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    current_catalogue = convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale))

    content = get_graphql_content(response)
    data = content["data"]["saleUpdate"]["sale"]
    assert data["endDate"] == end_date.isoformat()

    sale.refresh_from_db()
    assert sale.notification_sent_datetime == timezone.now()

    updated_webhook_mock.assert_called_once_with(
        sale, previous_catalogue, current_catalogue
    )
    sale_toggle_mock.assert_called_once_with(sale, current_catalogue)
    update_products_discounted_prices_of_catalogues_task_mock.assert_called_once()
    args, kwargs = update_products_discounted_prices_of_catalogues_task_mock.call_args
    assert set(kwargs["category_ids"]) == category_pks
    assert set(kwargs["collection_ids"]) == collection_pks
    assert set(kwargs["product_ids"]) == product_pks
    assert set(kwargs["variant_ids"]) == variant_pks


@patch(
    "saleor.product.tasks.update_products_discounted_prices_of_catalogues_task.delay"
)
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale_categories(
    updated_webhook_mock,
    update_products_discounted_prices_of_catalogues_task_mock,
    staff_api_client,
    sale,
    permission_manage_discounts,
    product_list,
    non_default_category,
):
    # given
    query = SALE_UPDATE_MUTATION

    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    category_pks = set(sale.categories.values_list("id", flat=True))

    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {
            "categories": [
                graphene.Node.to_global_id("Category", non_default_category.id)
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    current_catalogue = convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale))

    # then
    content = get_graphql_content(response)
    assert not content["data"]["saleUpdate"]["errors"]

    updated_webhook_mock.assert_called_once_with(
        sale, previous_catalogue, current_catalogue
    )
    args, kwargs = update_products_discounted_prices_of_catalogues_task_mock.call_args
    category_pks.add(non_default_category.id)
    assert set(kwargs["category_ids"]) == category_pks
    assert kwargs["collection_ids"] == []
    assert kwargs["product_ids"] == []
    assert kwargs["variant_ids"] == []


@patch(
    "saleor.product.tasks.update_products_discounted_prices_of_catalogues_task.delay"
)
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale_collections(
    updated_webhook_mock,
    update_products_discounted_prices_of_catalogues_task_mock,
    staff_api_client,
    sale,
    permission_manage_discounts,
    product_list,
    published_collection,
):
    # given
    query = SALE_UPDATE_MUTATION

    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    collection_pks = set(sale.collections.values_list("id", flat=True))

    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {
            "collections": [
                graphene.Node.to_global_id("Collection", published_collection.id)
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    current_catalogue = convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale))

    # then
    content = get_graphql_content(response)
    assert not content["data"]["saleUpdate"]["errors"]

    updated_webhook_mock.assert_called_once_with(
        sale, previous_catalogue, current_catalogue
    )
    args, kwargs = update_products_discounted_prices_of_catalogues_task_mock.call_args
    collection_pks.add(published_collection.id)
    assert kwargs["category_ids"] == []
    assert set(kwargs["collection_ids"]) == collection_pks
    assert kwargs["product_ids"] == []
    assert kwargs["variant_ids"] == []


@patch(
    "saleor.product.tasks.update_products_discounted_prices_of_catalogues_task.delay"
)
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale_variants(
    updated_webhook_mock,
    update_products_discounted_prices_of_catalogues_task_mock,
    staff_api_client,
    sale,
    permission_manage_discounts,
    product_list,
    preorder_variant_global_threshold,
):
    # given
    query = SALE_UPDATE_MUTATION

    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    variant_pks = set(sale.variants.values_list("id", flat=True))

    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {
            "variants": [
                graphene.Node.to_global_id(
                    "ProductVariant", preorder_variant_global_threshold.id
                )
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    current_catalogue = convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale))

    # then
    content = get_graphql_content(response)
    assert not content["data"]["saleUpdate"]["errors"]

    updated_webhook_mock.assert_called_once_with(
        sale, previous_catalogue, current_catalogue
    )
    args, kwargs = update_products_discounted_prices_of_catalogues_task_mock.call_args
    variant_pks.add(preorder_variant_global_threshold.id)
    assert kwargs["category_ids"] == []
    assert kwargs["collection_ids"] == []
    assert kwargs["product_ids"] == []
    assert set(kwargs["variant_ids"]) == variant_pks


@patch(
    "saleor.product.tasks.update_products_discounted_prices_of_catalogues_task.delay"
)
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale_products(
    updated_webhook_mock,
    update_products_discounted_prices_of_catalogues_task_mock,
    staff_api_client,
    sale,
    permission_manage_discounts,
    product_list,
    published_collection,
):
    # given
    query = SALE_UPDATE_MUTATION

    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    product_pks = set(sale.products.values_list("id", flat=True))

    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {
            "products": [graphene.Node.to_global_id("Product", product_list[-1].id)],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    current_catalogue = convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale))

    # then
    content = get_graphql_content(response)
    assert not content["data"]["saleUpdate"]["errors"]

    updated_webhook_mock.assert_called_once_with(
        sale, previous_catalogue, current_catalogue
    )
    args, kwargs = update_products_discounted_prices_of_catalogues_task_mock.call_args
    product_pks.add(product_list[-1].id)
    assert kwargs["category_ids"] == []
    assert kwargs["collection_ids"] == []
    assert set(kwargs["product_ids"]) == product_pks
    assert kwargs["variant_ids"] == []

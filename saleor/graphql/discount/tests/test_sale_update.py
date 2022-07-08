from datetime import timedelta
from unittest.mock import patch

import graphene
from django.utils import timezone
from freezegun import freeze_time

from ....discount import DiscountValueType
from ....discount.utils import fetch_catalogue_info
from ...tests.utils import get_graphql_content
from ..enums import DiscountValueTypeEnum
from ..mutations.utils import convert_catalogue_info_to_global_ids

SALE_UPDATE_MUTATION = """
    mutation  saleUpdate($id: ID!, $input: SaleInput!) {
        saleUpdate(id: $id, input: $input) {
            errors {
                field
                code
                message
            }
            sale {
                type
                startDate
                endDate
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale(
    updated_webhook_mock,
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
    product_ids = [
        graphene.Node.to_global_id("Product", product.id) for product in product_list
    ]
    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {
            "type": DiscountValueTypeEnum.PERCENTAGE.name,
            "products": product_ids,
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


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.plugins.manager.PluginsManager.sale_toggle")
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale_start_date_after_current_date_notification_not_sent(
    updated_webhook_mock,
    sale_toggle_mock,
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


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.plugins.manager.PluginsManager.sale_toggle")
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale_start_date_before_current_date_notification_already_sent(
    updated_webhook_mock,
    sale_toggle_mock,
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


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.plugins.manager.PluginsManager.sale_toggle")
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale_start_date_before_current_date_notification_sent(
    updated_webhook_mock,
    sale_toggle_mock,
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


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.plugins.manager.PluginsManager.sale_toggle")
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale_end_date_after_current_date_notification_not_sent(
    updated_webhook_mock,
    sale_toggle_mock,
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


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.plugins.manager.PluginsManager.sale_toggle")
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale_end_date_before_current_date_notification_already_sent(
    updated_webhook_mock,
    sale_toggle_mock,
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


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.plugins.manager.PluginsManager.sale_toggle")
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale_end_date_before_current_date_notification_sent(
    updated_webhook_mock,
    sale_toggle_mock,
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

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
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale_start_date_after_current_date_notification_flag_set_to_false(
    updated_webhook_mock,
    staff_api_client,
    sale,
    permission_manage_discounts,
):
    """Ensure the notification flag is changed to False when the start date is set
    after the current date and the flag was True before.
    """
    # given
    query = SALE_UPDATE_MUTATION

    sale.started_notification_sent = True
    sale.save(update_fields=["type", "started_notification_sent"])

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
    assert sale.started_notification_sent is False
    assert sale.ended_notification_sent is False

    updated_webhook_mock.assert_called_once_with(
        sale, previous_catalogue, current_catalogue
    )


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale_start_date_before_current_date_notification_flag_not_changed(
    updated_webhook_mock,
    staff_api_client,
    sale,
    permission_manage_discounts,
):
    """Ensure the notification flag is not changed when the start date is set before
    current date and notification was already sent.
    """
    # given
    query = SALE_UPDATE_MUTATION

    # Set discount value type to 'fixed' and change it in mutation
    sale.type = DiscountValueType.FIXED
    sale.started_notification_sent = True
    sale.save(update_fields=["type", "started_notification_sent"])

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
    assert sale.started_notification_sent is True
    assert sale.ended_notification_sent is False

    updated_webhook_mock.assert_called_once_with(
        sale, previous_catalogue, current_catalogue
    )


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.plugins.manager.PluginsManager.sale_started")
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale_start_date_before_current_date_notification_sent(
    updated_webhook_mock,
    sale_started_mock,
    staff_api_client,
    sale,
    permission_manage_discounts,
):
    """Ensure the sale_started notification is sent and the notification flag is updated
    when the start date is set before current date and the notification hasn't been sent
    before.
    """

    query = SALE_UPDATE_MUTATION

    # Set discount value type to 'fixed' and change it in mutation
    sale.type = DiscountValueType.FIXED
    sale.started_notification_sent = False
    sale.save(update_fields=["type", "started_notification_sent"])

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
    assert sale.started_notification_sent is True
    assert sale.ended_notification_sent is False

    updated_webhook_mock.assert_called_once_with(
        sale, previous_catalogue, current_catalogue
    )
    sale_started_mock.assert_called_once_with(sale, current_catalogue)


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale_end_date_after_current_date_notification_flag_set_to_false(
    updated_webhook_mock,
    staff_api_client,
    sale,
    permission_manage_discounts,
):
    """Ensure the notification flag is changed to False when the end date is set
    after the current date and the flag was True before.
    """
    # given
    query = SALE_UPDATE_MUTATION

    sale.ended_notification_sent = True
    sale.save(update_fields=["type", "ended_notification_sent"])

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
    assert sale.ended_notification_sent is False
    assert sale.ended_notification_sent is False

    updated_webhook_mock.assert_called_once_with(
        sale, previous_catalogue, current_catalogue
    )


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale_end_date_before_current_date_notification_flag_not_changed(
    updated_webhook_mock,
    staff_api_client,
    sale,
    permission_manage_discounts,
):
    """Ensure the notification flag is not changed when the end date is set before
    current date and notification was already sent.
    """
    # given
    query = SALE_UPDATE_MUTATION

    # Set discount value type to 'fixed' and change it in mutation
    sale.type = DiscountValueType.FIXED
    sale.ended_notification_sent = True
    sale.save(update_fields=["type", "ended_notification_sent"])

    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    end_date = timezone.now() - timedelta(days=1)
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
    assert sale.ended_notification_sent is True
    assert sale.started_notification_sent is False

    updated_webhook_mock.assert_called_once_with(
        sale, previous_catalogue, current_catalogue
    )


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.plugins.manager.PluginsManager.sale_ended")
@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_update_sale_end_date_before_current_date_notification_sent(
    updated_webhook_mock,
    sale_ended_mock,
    staff_api_client,
    sale,
    permission_manage_discounts,
):
    """Ensure the sale_ended notification is sent and the notification flag is updated
    when the end date is set before current date and the notification hasn't been sent
    before.
    """

    query = SALE_UPDATE_MUTATION

    # Set discount value type to 'fixed' and change it in mutation
    sale.type = DiscountValueType.FIXED
    sale.ended_notification_sent = False
    sale.save(update_fields=["type", "ended_notification_sent"])

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
    assert sale.ended_notification_sent is True
    assert sale.started_notification_sent is False

    updated_webhook_mock.assert_called_once_with(
        sale, previous_catalogue, current_catalogue
    )
    sale_ended_mock.assert_called_once_with(sale, current_catalogue)

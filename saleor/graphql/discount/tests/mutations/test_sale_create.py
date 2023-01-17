from datetime import timedelta
from unittest.mock import patch

import graphene
from django.utils import timezone
from freezegun import freeze_time

from .....discount import DiscountValueType
from .....discount.error_codes import DiscountErrorCode
from .....discount.models import Sale
from .....discount.utils import fetch_catalogue_info
from ....tests.utils import get_graphql_content
from ...enums import DiscountValueTypeEnum
from ...mutations.utils import convert_catalogue_info_to_global_ids

SALE_CREATE_MUTATION = """
    mutation saleCreate($input: SaleInput!) {
        saleCreate(input: $input) {
            sale {
                type
                name
                startDate
                endDate
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.plugins.manager.PluginsManager.sale_toggle")
@patch("saleor.plugins.manager.PluginsManager.sale_created")
def test_create_sale(
    created_webhook_mock,
    sale_toggle_mock,
    staff_api_client,
    permission_manage_discounts,
    product_list,
):
    # given
    query = SALE_CREATE_MUTATION
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)
    product_ids = [
        graphene.Node.to_global_id("Product", product.id) for product in product_list
    ]
    variables = {
        "input": {
            "name": "test sale",
            "type": DiscountValueTypeEnum.FIXED.name,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "products": product_ids,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["saleCreate"]["sale"]

    assert data["type"] == DiscountValueType.FIXED.upper()
    assert data["name"] == "test sale"
    assert data["startDate"] == start_date.isoformat()
    assert data["endDate"] == end_date.isoformat()

    sale = Sale.objects.filter(name="test sale").get()
    assert sale.notification_sent_datetime == timezone.now()

    current_catalogue = convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale))
    created_webhook_mock.assert_called_once_with(sale, current_catalogue)
    sale_toggle_mock.assert_called_once_with(sale, current_catalogue)


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.plugins.manager.PluginsManager.sale_toggle")
@patch("saleor.plugins.manager.PluginsManager.sale_created")
def test_create_sale_only_start_date(
    created_webhook_mock,
    sale_toggle_mock,
    staff_api_client,
    permission_manage_discounts,
    product_list,
):
    # given
    query = SALE_CREATE_MUTATION
    start_date = timezone.now() - timedelta(days=10)
    product_ids = [
        graphene.Node.to_global_id("Product", product.id) for product in product_list
    ]
    variables = {
        "input": {
            "name": "test sale",
            "type": DiscountValueTypeEnum.FIXED.name,
            "startDate": start_date.isoformat(),
            "products": product_ids,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["saleCreate"]["sale"]

    assert data["type"] == DiscountValueType.FIXED.upper()
    assert data["name"] == "test sale"
    assert data["startDate"] == start_date.isoformat()
    assert not data["endDate"]

    sale = Sale.objects.filter(name="test sale").get()
    assert sale.notification_sent_datetime == timezone.now()

    current_catalogue = convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale))
    created_webhook_mock.assert_called_once_with(sale, current_catalogue)
    sale_toggle_mock.assert_called_once_with(sale, current_catalogue)


def test_create_sale_with_enddate_before_startdate(
    staff_api_client, permission_manage_discounts
):
    # given
    query = SALE_CREATE_MUTATION
    start_date = timezone.now() + timedelta(days=365)
    end_date = timezone.now() - timedelta(days=365)
    variables = {
        "input": {
            "name": "test sale",
            "type": DiscountValueTypeEnum.FIXED.name,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["saleCreate"]["errors"]
    errors = content["data"]["saleCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "endDate"
    assert errors[0]["code"] == DiscountErrorCode.INVALID.name


@patch("saleor.plugins.manager.PluginsManager.sale_toggle")
@patch("saleor.plugins.manager.PluginsManager.sale_created")
def test_create_sale_start_date_and_end_date_before_current_date(
    created_webhook_mock,
    sale_toggle_mock,
    staff_api_client,
    permission_manage_discounts,
    product_list,
):
    """Ensure the notification is sent when the sale is created with start
    and end date that already passed."""
    # given
    query = SALE_CREATE_MUTATION
    start_date = timezone.now() - timedelta(days=20)
    end_date = timezone.now() - timedelta(days=10)
    product_ids = [
        graphene.Node.to_global_id("Product", product.id) for product in product_list
    ]
    variables = {
        "input": {
            "name": "test sale",
            "type": DiscountValueTypeEnum.FIXED.name,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "products": product_ids,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["saleCreate"]["sale"]

    assert data["type"] == DiscountValueType.FIXED.upper()
    assert data["name"] == "test sale"
    assert data["startDate"] == start_date.isoformat()
    assert data["endDate"] == end_date.isoformat()

    sale = Sale.objects.filter(name="test sale").get()
    assert sale.notification_sent_datetime is None

    current_catalogue = convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale))
    created_webhook_mock.assert_called_once_with(sale, current_catalogue)
    sale_toggle_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.sale_toggle")
@patch("saleor.plugins.manager.PluginsManager.sale_created")
def test_create_sale_start_date_and_end_date_after_current_date(
    created_webhook_mock,
    sale_toggle_mock,
    staff_api_client,
    permission_manage_discounts,
    product_list,
):
    """Ensure the notification is not sent when the sale is created with start
    and end date in the feature."""
    # given
    query = SALE_CREATE_MUTATION
    start_date = timezone.now() + timedelta(days=10)
    end_date = timezone.now() + timedelta(days=20)
    product_ids = [
        graphene.Node.to_global_id("Product", product.id) for product in product_list
    ]
    variables = {
        "input": {
            "name": "test sale",
            "type": DiscountValueTypeEnum.FIXED.name,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "products": product_ids,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["saleCreate"]["sale"]

    assert data["type"] == DiscountValueType.FIXED.upper()
    assert data["name"] == "test sale"
    assert data["startDate"] == start_date.isoformat()
    assert data["endDate"] == end_date.isoformat()

    sale = Sale.objects.filter(name="test sale").get()
    assert sale.notification_sent_datetime is None

    current_catalogue = convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale))
    created_webhook_mock.assert_called_once_with(sale, current_catalogue)
    sale_toggle_mock.assert_not_called()

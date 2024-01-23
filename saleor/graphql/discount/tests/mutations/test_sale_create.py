from datetime import timedelta
from unittest.mock import patch

import graphene
from django.utils import timezone
from freezegun import freeze_time

from .....discount import DiscountValueType
from .....discount.error_codes import DiscountErrorCode
from .....discount.models import Promotion, PromotionRule
from ....tests.utils import get_graphql_content
from ...enums import DiscountValueTypeEnum
from ...utils import convert_migrated_sale_predicate_to_catalogue_info

SALE_CREATE_MUTATION = """
    mutation saleCreate($input: SaleInput!) {
        saleCreate(input: $input) {
            sale {
                id
                type
                name
                startDate
                endDate
                products(first: 10) {
                    edges {
                        node {
                            id
                        }
                    }
                }
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
    sale = Promotion.objects.filter(name="test sale").get()
    rules = PromotionRule.objects.filter(promotion_id=sale.id).all()
    assert len(rules) == 1
    rule = rules[0]

    assert data["type"] == DiscountValueType.FIXED.upper()
    assert data["name"] == "test sale"
    assert data["startDate"] == start_date.isoformat()
    assert data["endDate"] == end_date.isoformat()
    assert len(data["products"]["edges"]) == len(product_list)
    assert {edge["node"]["id"] for edge in data["products"]["edges"]} == set(
        product_ids
    )
    type, id = graphene.Node.from_global_id(data["id"])
    assert type == "Sale"
    assert str(sale.old_sale_id) == id
    assert sale.last_notification_scheduled_at == timezone.now()
    assert rule.reward_value_type == DiscountValueTypeEnum.FIXED.value

    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(
        rule.catalogue_predicate
    )
    created_webhook_mock.assert_called_once_with(sale, current_catalogue)
    sale_toggle_mock.assert_called_once_with(sale, current_catalogue)

    for rule in sale.rules.all():
        assert rule.variants_dirty is True


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
    sale = Promotion.objects.filter(name="test sale").get()
    rule = PromotionRule.objects.filter(promotion_id=sale.id).get()

    assert data["type"] == DiscountValueType.FIXED.upper()
    assert data["name"] == "test sale"
    assert data["startDate"] == start_date.isoformat()
    assert not data["endDate"]
    assert sale.last_notification_scheduled_at == timezone.now()

    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(
        rule.catalogue_predicate
    )
    created_webhook_mock.assert_called_once_with(sale, current_catalogue)
    sale_toggle_mock.assert_called_once_with(sale, current_catalogue)
    for rule in sale.rules.all():
        assert rule.variants_dirty is True


def test_create_sale_with_end_date_before_startdate(
    staff_api_client,
    permission_manage_discounts,
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
    sale = Promotion.objects.filter(name="test sale").get()
    rule = PromotionRule.objects.filter(promotion_id=sale.id).get()

    assert data["type"] == DiscountValueType.FIXED.upper()
    assert data["name"] == "test sale"
    assert data["startDate"] == start_date.isoformat()
    assert data["endDate"] == end_date.isoformat()
    assert sale.last_notification_scheduled_at is None

    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(
        rule.catalogue_predicate
    )
    created_webhook_mock.assert_called_once_with(sale, current_catalogue)
    sale_toggle_mock.assert_not_called()
    for rule in sale.rules.all():
        assert rule.variants_dirty is True


@patch("saleor.plugins.manager.PluginsManager.sale_toggle")
@patch("saleor.plugins.manager.PluginsManager.sale_created")
def test_create_sale_start_date_and_end_date_after_current_date(
    created_webhook_mock,
    sale_toggle_mock,
    staff_api_client,
    permission_manage_discounts,
    product_list,
):
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
    sale = Promotion.objects.filter(name="test sale").get()
    rule = PromotionRule.objects.filter(promotion_id=sale.id).get()

    assert data["type"] == DiscountValueType.FIXED.upper()
    assert data["name"] == "test sale"
    assert data["startDate"] == start_date.isoformat()
    assert data["endDate"] == end_date.isoformat()
    assert sale.last_notification_scheduled_at is None

    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(
        rule.catalogue_predicate
    )
    created_webhook_mock.assert_called_once_with(sale, current_catalogue)
    sale_toggle_mock.assert_not_called()
    for rule in sale.rules.all():
        assert rule.variants_dirty is True


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.plugins.manager.PluginsManager.sale_toggle")
@patch("saleor.plugins.manager.PluginsManager.sale_created")
def test_create_sale_empty_predicate(
    created_webhook_mock,
    sale_toggle_mock,
    staff_api_client,
    permission_manage_discounts,
):
    # given
    query = SALE_CREATE_MUTATION
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)
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
    data = content["data"]["saleCreate"]["sale"]
    sale = Promotion.objects.filter(name="test sale").get()
    rules = PromotionRule.objects.filter(promotion_id=sale.id).all()
    assert len(rules) == 1
    rule = rules[0]

    assert data["type"] == DiscountValueType.FIXED.upper()
    assert data["name"] == "test sale"
    assert data["startDate"] == start_date.isoformat()
    assert data["endDate"] == end_date.isoformat()
    assert not data["products"]
    type, id = graphene.Node.from_global_id(data["id"])
    assert type == "Sale"
    assert str(sale.old_sale_id) == id
    assert sale.last_notification_scheduled_at == timezone.now()
    assert rule.reward_value_type == DiscountValueTypeEnum.FIXED.value
    assert not rule.catalogue_predicate

    current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(
        rule.catalogue_predicate
    )
    created_webhook_mock.assert_called_once_with(sale, current_catalogue)
    sale_toggle_mock.assert_called_once_with(sale, current_catalogue)

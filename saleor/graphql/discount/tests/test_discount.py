import json
from datetime import timedelta
from unittest.mock import ANY, patch

import graphene
import pytest
from django.utils import timezone
from django.utils.functional import SimpleLazyObject
from django_countries import countries
from freezegun import freeze_time

from ....core.utils.json_serializer import CustomJsonEncoder
from ....discount import DiscountValueType, VoucherType
from ....discount.error_codes import DiscountErrorCode
from ....discount.models import Sale, SaleChannelListing, Voucher
from ....discount.utils import fetch_catalogue_info
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.payloads import generate_meta, generate_requestor
from ...tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from ..enums import DiscountValueTypeEnum, VoucherTypeEnum
from ..mutations.utils import convert_catalogue_info_to_global_ids


@pytest.fixture
def voucher_with_many_channels_and_countries(voucher_with_many_channels):
    voucher_with_many_channels.countries = countries
    voucher_with_many_channels.save(update_fields=["countries"])
    return voucher_with_many_channels


@pytest.fixture
def query_vouchers_with_filter():
    query = """
    query ($filter: VoucherFilterInput!, ) {
      vouchers(first:5, filter: $filter){
        edges{
          node{
            id
            name
            startDate
          }
        }
      }
    }
    """
    return query


@pytest.fixture
def query_sales_with_filter():
    query = """
    query ($filter: SaleFilterInput!, ) {
      sales(first:5, filter: $filter){
        edges{
          node{
            id
            name
            startDate
          }
        }
      }
    }
    """
    return query


def test_voucher_query(
    staff_api_client,
    voucher,
    product,
    permission_manage_discounts,
    permission_manage_products,
):
    query = """
    query vouchers {
        vouchers(first: 1) {
            edges {
                node {
                    type
                    name
                    code
                    usageLimit
                    used
                    startDate
                    discountValueType
                    applyOncePerCustomer
                    products(first: 1) {
                        edges {
                            node {
                                name
                            }
                        }
                    }
                    countries {
                        code
                        country
                    }
                    channelListings {
                        id
                        channel {
                            slug
                        }
                        discountValue
                        currency
                    }
                }
            }
        }
    }
    """
    voucher.products.add(product)

    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_discounts, permission_manage_products]
    )

    content = get_graphql_content(response)
    data = content["data"]["vouchers"]["edges"][0]["node"]

    assert data["type"] == voucher.type.upper()
    assert data["name"] == voucher.name
    assert data["code"] == voucher.code
    assert data["usageLimit"] == voucher.usage_limit
    assert data["products"]["edges"][0]["node"]["name"] == product.name

    assert data["applyOncePerCustomer"] == voucher.apply_once_per_customer
    assert data["used"] == voucher.used
    assert data["startDate"] == voucher.start_date.isoformat()
    assert data["discountValueType"] == voucher.discount_value_type.upper()
    assert data["countries"] == [
        {"country": country.name, "code": country.code} for country in voucher.countries
    ]
    channel_listing = voucher.channel_listings.first()
    assert {
        "id": ANY,
        "channel": {"slug": channel_listing.channel.slug},
        "discountValue": channel_listing.discount_value,
        "currency": channel_listing.channel.currency_code,
    } in data["channelListings"]


def test_voucher_query_with_channel_slug(
    staff_api_client,
    voucher_with_many_channels_and_countries,
    permission_manage_discounts,
    channel_USD,
    product,
):
    voucher = voucher_with_many_channels_and_countries
    voucher.products.add(product)

    query = """
    query vouchers($channel: String) {
        vouchers(first: 1, channel: $channel) {
            edges {
                node {
                    type
                    name
                    code
                    usageLimit
                    used
                    startDate
                    discountValueType
                    applyOncePerCustomer
                    products(first: 1) {
                        edges {
                            node {
                                name
                            }
                        }
                    }
                    countries {
                        code
                        country
                    }
                    channelListings {
                        id
                        channel {
                            slug
                        }
                        discountValue
                        currency
                    }
                }
            }
        }
    }
    """
    variables = {"channel": channel_USD.slug}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["vouchers"]["edges"][0]["node"]

    assert data["type"] == voucher.type.upper()
    assert data["name"] == voucher.name
    assert data["code"] == voucher.code
    assert data["products"]["edges"][0]["node"]["name"] == product.name
    assert data["usageLimit"] == voucher.usage_limit
    assert data["applyOncePerCustomer"] == voucher.apply_once_per_customer
    assert data["used"] == voucher.used
    assert data["startDate"] == voucher.start_date.isoformat()
    assert data["discountValueType"] == voucher.discount_value_type.upper()
    assert data["countries"] == [
        {"country": country.name, "code": country.code} for country in voucher.countries
    ]
    assert len(data["channelListings"]) == 2
    for channel_listing in voucher.channel_listings.all():
        assert {
            "id": ANY,
            "channel": {"slug": channel_listing.channel.slug},
            "discountValue": channel_listing.discount_value,
            "currency": channel_listing.channel.currency_code,
        } in data["channelListings"]


def test_vouchers_query_with_channel_slug(
    staff_api_client,
    voucher_percentage,
    voucher_with_many_channels,
    permission_manage_discounts,
    channel_PLN,
    product,
):

    query = """
    query vouchers($channel: String) {
        vouchers(first: 2, channel: $channel) {
            edges {
                node {
                    name
                }
            }
        }
    }
    """
    variables = {"channel": channel_PLN.slug}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    assert len(content["data"]["vouchers"]["edges"]) == 1


def test_vouchers_query(
    staff_api_client,
    voucher_percentage,
    voucher_with_many_channels,
    permission_manage_discounts,
    channel_PLN,
    product,
):

    query = """
    query vouchers {
        vouchers(first: 2) {
            edges {
                node {
                    name
                }
            }
        }
    }
    """

    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    assert len(content["data"]["vouchers"]["edges"]) == 2


def test_sale_query(
    staff_api_client,
    sale,
    permission_manage_discounts,
    channel_USD,
    permission_manage_products,
):
    query = """
        query sales {
            sales(first: 1) {
                edges {
                    node {
                        type
                        products(first: 1) {
                            edges {
                                node {
                                    name
                                }
                            }
                        }
                        collections(first: 1) {
                            edges {
                                node {
                                    slug
                                }
                            }
                        }
                        name
                        channelListings {
                            discountValue
                        }
                        startDate
                    }
                }
            }
        }
        """
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_discounts, permission_manage_products]
    )
    channel_listing_usd = sale.channel_listings.get(channel=channel_USD)
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"][0]["node"]
    assert data["products"]["edges"][0]["node"]["name"] == sale.products.first().name

    assert data["type"] == sale.type.upper()
    assert data["name"] == sale.name
    assert (
        data["channelListings"][0]["discountValue"]
        == channel_listing_usd.discount_value
    )
    assert data["startDate"] == sale.start_date.isoformat()


def test_sale_query_with_channel_slug(
    staff_api_client, sale, permission_manage_discounts, channel_USD
):
    query = """
        query sales($channel: String) {
            sales(first: 1, channel: $channel) {
                edges {
                    node {
                        type
                        products(first: 1) {
                            edges {
                                node {
                                    name
                                }
                            }
                        }
                        discountValue
                        name
                        channelListings {
                            discountValue
                        }
                        startDate
                    }
                }
            }
        }
        """
    variables = {"channel": channel_USD.slug}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    channel_listing = sale.channel_listings.get()
    content = get_graphql_content(response)

    data = content["data"]["sales"]["edges"][0]["node"]

    assert data["type"] == sale.type.upper()
    assert data["name"] == sale.name
    assert data["products"]["edges"][0]["node"]["name"] == sale.products.first().name
    assert data["discountValue"] == channel_listing.discount_value
    assert data["channelListings"][0]["discountValue"] == channel_listing.discount_value
    assert data["startDate"] == sale.start_date.isoformat()


def test_sales_query(
    staff_api_client,
    sale_with_many_channels,
    sale,
    permission_manage_discounts,
    channel_USD,
    permission_manage_products,
):
    query = """
        query sales {
            sales(first: 2) {
                edges {
                    node {
                        name
                    }
                }
            }
        }
        """
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_discounts, permission_manage_products]
    )
    content = get_graphql_content(response)

    assert len(content["data"]["sales"]["edges"]) == 2


def test_sales_query_with_channel_slug(
    staff_api_client,
    sale_with_many_channels,
    sale,
    permission_manage_discounts,
    channel_PLN,
    permission_manage_products,
):
    query = """
        query sales($channel: String) {
            sales(first: 2, channel: $channel) {
                edges {
                    node {
                        name
                    }
                }
            }
        }
        """
    variables = {"channel": channel_PLN.slug}
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_discounts, permission_manage_products],
    )
    content = get_graphql_content(response)

    assert len(content["data"]["sales"]["edges"]) == 1


CREATE_VOUCHER_MUTATION = """
mutation  voucherCreate(
    $type: VoucherTypeEnum, $name: String, $code: String,
    $discountValueType: DiscountValueTypeEnum, $usageLimit: Int,
    $minCheckoutItemsQuantity: Int, $startDate: DateTime, $endDate: DateTime,
    $applyOncePerOrder: Boolean, $applyOncePerCustomer: Boolean) {
        voucherCreate(input: {
                name: $name, type: $type, code: $code,
                discountValueType: $discountValueType,
                minCheckoutItemsQuantity: $minCheckoutItemsQuantity,
                startDate: $startDate, endDate: $endDate, usageLimit: $usageLimit
                applyOncePerOrder: $applyOncePerOrder,
                applyOncePerCustomer: $applyOncePerCustomer}) {
            errors {
                field
                code
                message
            }
            voucher {
                type
                minCheckoutItemsQuantity
                name
                code
                discountValueType
                startDate
                endDate
                applyOncePerOrder
                applyOncePerCustomer
            }
        }
    }
"""


def test_create_voucher(staff_api_client, permission_manage_discounts):
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)
    variables = {
        "name": "test voucher",
        "type": VoucherTypeEnum.ENTIRE_ORDER.name,
        "code": "testcode123",
        "discountValueType": DiscountValueTypeEnum.FIXED.name,
        "minCheckoutItemsQuantity": 10,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "applyOncePerOrder": True,
        "applyOncePerCustomer": True,
        "usageLimit": 3,
    }

    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    get_graphql_content(response)
    voucher = Voucher.objects.get()
    assert voucher.type == VoucherType.ENTIRE_ORDER
    assert voucher.name == "test voucher"
    assert voucher.code == "testcode123"
    assert voucher.discount_value_type == DiscountValueType.FIXED
    assert voucher.start_date == start_date
    assert voucher.end_date == end_date
    assert voucher.apply_once_per_order
    assert voucher.apply_once_per_customer
    assert voucher.usage_limit == 3


@freeze_time("2022-05-12 12:00:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_create_voucher_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    permission_manage_discounts,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)
    variables = {
        "name": "test voucher",
        "type": VoucherTypeEnum.ENTIRE_ORDER.name,
        "code": "testcode123",
        "discountValueType": DiscountValueTypeEnum.FIXED.name,
        "minCheckoutItemsQuantity": 10,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "applyOncePerOrder": True,
        "applyOncePerCustomer": True,
        "usageLimit": 3,
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    voucher = Voucher.objects.last()

    # then
    assert content["data"]["voucherCreate"]["voucher"]
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": graphene.Node.to_global_id("Voucher", voucher.id),
                "name": voucher.name,
                "code": voucher.code,
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.VOUCHER_CREATED,
        [any_webhook],
        voucher,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_create_voucher_with_empty_code(staff_api_client, permission_manage_discounts):
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)
    variables = {
        "name": "test voucher",
        "type": VoucherTypeEnum.ENTIRE_ORDER.name,
        "code": "",
        "discountValueType": DiscountValueTypeEnum.FIXED.name,
        "discountValue": 10.12,
        "minAmountSpent": 1.12,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "usageLimit": None,
    }

    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCreate"]["voucher"]
    assert data["name"] == variables["name"]
    assert data["code"] != ""


def test_create_voucher_with_existing_gift_card_code(
    staff_api_client, gift_card, permission_manage_discounts
):
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)
    variables = {
        "name": "test voucher",
        "type": VoucherTypeEnum.ENTIRE_ORDER.name,
        "code": gift_card.code,
        "discountValueType": DiscountValueTypeEnum.FIXED.name,
        "discountValue": 10.12,
        "minAmountSpent": 1.12,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "usageLimit": 3,
    }

    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    assert content["data"]["voucherCreate"]["errors"]
    errors = content["data"]["voucherCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "code"
    assert errors[0]["code"] == DiscountErrorCode.ALREADY_EXISTS.name


def test_create_voucher_with_existing_voucher_code(
    staff_api_client, voucher_shipping_type, permission_manage_discounts
):
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)
    variables = {
        "name": "test voucher",
        "type": VoucherTypeEnum.ENTIRE_ORDER.name,
        "code": voucher_shipping_type.code,
        "discountValueType": DiscountValueTypeEnum.FIXED.name,
        "discountValue": 10.12,
        "minAmountSpent": 1.12,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "usageLimit": 3,
    }
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    assert content["data"]["voucherCreate"]["errors"]
    errors = content["data"]["voucherCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "code"
    assert errors


def test_create_voucher_with_enddate_before_startdate(
    staff_api_client, voucher_shipping_type, permission_manage_discounts
):
    start_date = timezone.now() + timedelta(days=365)
    end_date = timezone.now() - timedelta(days=365)
    variables = {
        "name": "test voucher",
        "type": VoucherTypeEnum.ENTIRE_ORDER.name,
        "code": "FUTURE",
        "discountValueType": DiscountValueTypeEnum.FIXED.name,
        "discountValue": 10.12,
        "minAmountSpent": 1.12,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "usageLimit": 3,
    }
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    assert content["data"]["voucherCreate"]["errors"]
    errors = content["data"]["voucherCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "endDate"
    assert errors[0]["code"] == DiscountErrorCode.INVALID.name
    assert errors


UPDATE_VOUCHER_MUTATION = """
    mutation  voucherUpdate($code: String,
        $discountValueType: DiscountValueTypeEnum, $id: ID!,
        $applyOncePerOrder: Boolean, $minCheckoutItemsQuantity: Int) {
            voucherUpdate(id: $id, input: {
                code: $code, discountValueType: $discountValueType,
                applyOncePerOrder: $applyOncePerOrder,
                minCheckoutItemsQuantity: $minCheckoutItemsQuantity
                }) {
                errors {
                    field
                    code
                    message
                }
                voucher {
                    code
                    discountValueType
                    applyOncePerOrder
                    minCheckoutItemsQuantity
                }
            }
        }
"""


def test_update_voucher(staff_api_client, voucher, permission_manage_discounts):
    apply_once_per_order = not voucher.apply_once_per_order
    # Set discount value type to 'fixed' and change it in mutation
    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.save()
    assert voucher.code != "testcode123"
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "code": "testcode123",
        "discountValueType": DiscountValueTypeEnum.PERCENTAGE.name,
        "applyOncePerOrder": apply_once_per_order,
        "minCheckoutItemsQuantity": 10,
    }

    response = staff_api_client.post_graphql(
        UPDATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherUpdate"]["voucher"]
    assert data["code"] == "testcode123"
    assert data["discountValueType"] == DiscountValueType.PERCENTAGE.upper()
    assert data["applyOncePerOrder"] == apply_once_per_order
    assert data["minCheckoutItemsQuantity"] == 10


@freeze_time("2022-05-12 12:00:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_update_voucher_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    voucher,
    permission_manage_discounts,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "code": "testcode123",
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["voucherUpdate"]["voucher"]
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": variables["id"],
                "name": voucher.name,
                "code": variables["code"],
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.VOUCHER_UPDATED,
        [any_webhook],
        voucher,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


VOUCHER_DELETE_MUTATION = """
    mutation DeleteVoucher($id: ID!) {
        voucherDelete(id: $id) {
            voucher {
                name
                id
            }
            errors {
                field
                code
                message
            }
          }
        }
"""


def test_voucher_delete_mutation(
    staff_api_client, voucher, permission_manage_discounts
):
    variables = {"id": graphene.Node.to_global_id("Voucher", voucher.id)}

    response = staff_api_client.post_graphql(
        VOUCHER_DELETE_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherDelete"]
    assert data["voucher"]["name"] == voucher.name
    with pytest.raises(voucher._meta.model.DoesNotExist):
        voucher.refresh_from_db()


@freeze_time("2022-05-12 12:00:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_voucher_delete_mutation_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    voucher,
    permission_manage_discounts,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    variables = {"id": graphene.Node.to_global_id("Voucher", voucher.id)}

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_DELETE_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["voucherDelete"]["voucher"]
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": variables["id"],
                "name": voucher.name,
                "code": voucher.code,
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.VOUCHER_DELETED,
        [any_webhook],
        voucher,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


VOUCHER_ADD_CATALOGUES_MUTATION = """
    mutation voucherCataloguesAdd($id: ID!, $input: CatalogueInput!) {
        voucherCataloguesAdd(id: $id, input: $input) {
            voucher {
                name
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_voucher_add_catalogues(
    staff_api_client,
    voucher,
    category,
    product,
    collection,
    product_variant_list,
    permission_manage_discounts,
):
    product_id = graphene.Node.to_global_id("Product", product.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    variant_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.id)
        for variant in product_variant_list
    ]
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {
            "products": [product_id],
            "collections": [collection_id],
            "categories": [category_id],
            "variants": variant_ids,
        },
    }

    response = staff_api_client.post_graphql(
        VOUCHER_ADD_CATALOGUES_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCataloguesAdd"]

    assert not data["errors"]
    assert product in voucher.products.all()
    assert category in voucher.categories.all()
    assert collection in voucher.collections.all()
    assert set(product_variant_list) == set(voucher.variants.all())


@freeze_time("2022-05-12 12:00:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_voucher_add_catalogues_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    voucher,
    category,
    product,
    collection,
    product_variant_list,
    permission_manage_discounts,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    product_id = graphene.Node.to_global_id("Product", product.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    variant_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.id)
        for variant in product_variant_list
    ]
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {
            "products": [product_id],
            "collections": [collection_id],
            "categories": [category_id],
            "variants": variant_ids,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_ADD_CATALOGUES_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCataloguesAdd"]

    # then
    assert content["data"]["voucherCataloguesAdd"]["voucher"]
    assert not data["errors"]
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": variables["id"],
                "name": voucher.name,
                "code": voucher.code,
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.VOUCHER_UPDATED,
        [any_webhook],
        voucher,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_voucher_add_catalogues_with_product_without_variant(
    staff_api_client,
    voucher,
    category,
    product,
    collection,
    permission_manage_discounts,
):
    query = """
        mutation voucherCataloguesAdd($id: ID!, $input: CatalogueInput!) {
            voucherCataloguesAdd(id: $id, input: $input) {
                voucher {
                    name
                }
                errors {
                    field
                    code
                    message
                }
            }
        }
    """
    product.variants.all().delete()
    product_id = graphene.Node.to_global_id("Product", product.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {
            "products": [product_id],
            "collections": [collection_id],
            "categories": [category_id],
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    error = content["data"]["voucherCataloguesAdd"]["errors"][0]

    assert error["code"] == DiscountErrorCode.CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT.name
    assert error["message"] == "Cannot manage products without variants."


VOUCHER_REMOVE_CATALOGUES = """
    mutation voucherCataloguesRemove($id: ID!, $input: CatalogueInput!) {
        voucherCataloguesRemove(id: $id, input: $input) {
            voucher {
                name
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_voucher_remove_catalogues(
    staff_api_client,
    voucher,
    category,
    product,
    collection,
    product_variant_list,
    permission_manage_discounts,
):
    voucher.products.add(product)
    voucher.collections.add(collection)
    voucher.categories.add(category)
    voucher.variants.add(*product_variant_list)

    product_id = graphene.Node.to_global_id("Product", product.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    variant_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.id)
        for variant in product_variant_list
    ]
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {
            "products": [product_id],
            "collections": [collection_id],
            "categories": [category_id],
            "variants": variant_ids,
        },
    }

    response = staff_api_client.post_graphql(
        VOUCHER_REMOVE_CATALOGUES, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCataloguesRemove"]
    voucher_variants = list(voucher.variants.all())

    assert not data["errors"]
    assert product not in voucher.products.all()
    assert category not in voucher.categories.all()
    assert collection not in voucher.collections.all()
    assert not any(v in voucher_variants for v in product_variant_list)


def test_voucher_add_no_catalogues(
    staff_api_client, voucher, permission_manage_discounts
):
    query = """
        mutation voucherCataloguesAdd($id: ID!, $input: CatalogueInput!) {
            voucherCataloguesAdd(id: $id, input: $input) {
                voucher {
                    name
                }
                errors {
                    field
                    code
                    message
                }
            }
        }
    """
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {"products": [], "collections": [], "categories": [], "variants": []},
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCataloguesAdd"]

    assert not data["errors"]
    assert not voucher.products.exists()
    assert not voucher.categories.exists()
    assert not voucher.collections.exists()
    assert not voucher.variants.exists()


def test_voucher_remove_no_catalogues(
    staff_api_client,
    voucher,
    category,
    product,
    collection,
    product_variant_list,
    permission_manage_discounts,
):
    voucher.products.add(product)
    voucher.collections.add(collection)
    voucher.categories.add(category)
    voucher.variants.add(*product_variant_list)

    query = """
        mutation voucherCataloguesAdd($id: ID!, $input: CatalogueInput!) {
            voucherCataloguesAdd(id: $id, input: $input) {
                voucher {
                    name
                }
                errors {
                    field
                    code
                    message
                }
            }
        }
    """
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {"products": [], "collections": [], "categories": [], "variants": []},
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCataloguesAdd"]

    assert not data["errors"]
    assert voucher.products.exists()
    assert voucher.categories.exists()
    assert voucher.collections.exists()
    assert voucher.variants.exists()


@patch("saleor.plugins.manager.PluginsManager.sale_deleted")
def test_sale_delete_mutation(
    deleted_webhook_mock, staff_api_client, sale, permission_manage_discounts
):
    query = """
        mutation DeleteSale($id: ID!) {
            saleDelete(id: $id) {
                sale {
                    name
                    id
                }
                errors {
                    field
                    code
                    message
                }
              }
            }
    """
    variables = {"id": graphene.Node.to_global_id("Sale", sale.id)}
    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["saleDelete"]
    assert data["sale"]["name"] == sale.name
    deleted_webhook_mock.assert_called_once_with(sale, previous_catalogue)
    with pytest.raises(sale._meta.model.DoesNotExist):
        sale.refresh_from_db()


@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_sale_add_catalogues(
    updated_webhook_mock,
    staff_api_client,
    sale,
    category,
    product,
    collection,
    variant,
    product_variant_list,
    permission_manage_discounts,
):
    query = """
        mutation saleCataloguesAdd($id: ID!, $input: CatalogueInput!) {
            saleCataloguesAdd(id: $id, input: $input) {
                sale {
                    name
                }
                errors {
                    field
                    code
                    message
                }
            }
        }
    """
    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    product_id = graphene.Node.to_global_id("Product", product.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    variant_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.id)
        for variant in product_variant_list
    ]
    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {
            "products": [product_id],
            "collections": [collection_id],
            "categories": [category_id],
            "variants": variant_ids,
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    current_catalogue = convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale))
    content = get_graphql_content(response)
    data = content["data"]["saleCataloguesAdd"]

    assert not data["errors"]
    assert product in sale.products.all()
    assert category in sale.categories.all()
    assert collection in sale.collections.all()
    assert set(product_variant_list + [variant]) == set(sale.variants.all())

    updated_webhook_mock.assert_called_once_with(
        sale, previous_catalogue=previous_catalogue, current_catalogue=current_catalogue
    )


def test_sale_add_catalogues_with_product_without_variants(
    staff_api_client, sale, category, product, collection, permission_manage_discounts
):
    query = """
        mutation saleCataloguesAdd($id: ID!, $input: CatalogueInput!) {
            saleCataloguesAdd(id: $id, input: $input) {
                sale {
                    name
                }
                errors {
                    field
                    code
                    message
                }
            }
        }
    """
    product.variants.all().delete()
    product_id = graphene.Node.to_global_id("Product", product.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)

    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {
            "products": [product_id],
            "collections": [collection_id],
            "categories": [category_id],
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    error = content["data"]["saleCataloguesAdd"]["errors"][0]

    assert error["code"] == DiscountErrorCode.CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT.name
    assert error["message"] == "Cannot manage products without variants."


@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_sale_remove_catalogues(
    updated_webhook_mock,
    staff_api_client,
    sale,
    category,
    product,
    collection,
    product_variant_list,
    permission_manage_discounts,
):
    sale.products.add(product)
    sale.collections.add(collection)
    sale.categories.add(category)
    sale.variants.add(*product_variant_list)

    query = """
        mutation saleCataloguesRemove($id: ID!, $input: CatalogueInput!) {
            saleCataloguesRemove(id: $id, input: $input) {
                sale {
                    name
                }
                errors {
                    field
                    code
                    message
                }
            }
        }
    """
    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    product_id = graphene.Node.to_global_id("Product", product.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    variant_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.id)
        for variant in product_variant_list
    ]
    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {
            "products": [product_id],
            "collections": [collection_id],
            "categories": [category_id],
            "variants": variant_ids,
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    current_catalogue = convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale))

    content = get_graphql_content(response)
    data = content["data"]["saleCataloguesRemove"]
    product_variants = list(sale.variants.all())

    assert not data["errors"]
    assert product not in sale.products.all()
    assert category not in sale.categories.all()
    assert collection not in sale.collections.all()
    assert not any(v in product_variants for v in product_variant_list)

    updated_webhook_mock.assert_called_once_with(
        sale, previous_catalogue=previous_catalogue, current_catalogue=current_catalogue
    )


def test_sale_add_no_catalogues(
    staff_api_client, new_sale, permission_manage_discounts
):
    query = """
        mutation saleCataloguesAdd($id: ID!, $input: CatalogueInput!) {
            saleCataloguesAdd(id: $id, input: $input) {
                sale {
                    name
                }
                errors {
                    field
                    code
                    message
                }
            }
        }
    """
    variables = {
        "id": graphene.Node.to_global_id("Sale", new_sale.id),
        "input": {"products": [], "collections": [], "categories": [], "variants": []},
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["saleCataloguesAdd"]

    assert not data["errors"]
    assert not new_sale.products.exists()
    assert not new_sale.categories.exists()
    assert not new_sale.collections.exists()
    assert not new_sale.variants.exists()


def test_sale_remove_no_catalogues(
    staff_api_client,
    sale,
    category,
    product,
    collection,
    product_variant_list,
    permission_manage_discounts,
):
    sale.products.add(product)
    sale.collections.add(collection)
    sale.categories.add(category)
    sale.variants.add(*product_variant_list)

    query = """
        mutation saleCataloguesAdd($id: ID!, $input: CatalogueInput!) {
            saleCataloguesAdd(id: $id, input: $input) {
                sale {
                    name
                }
                errors {
                    field
                    code
                    message
                }
            }
        }
    """
    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {"products": [], "collections": [], "categories": [], "variants": []},
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["saleCataloguesAdd"]

    assert not data["errors"]
    assert sale.products.exists()
    assert sale.categories.exists()
    assert sale.collections.exists()
    assert sale.variants.exists()


@pytest.mark.parametrize(
    "voucher_filter, start_date, end_date, count",
    [
        (
            {"status": "ACTIVE"},
            timezone.now().replace(year=2015, month=1, day=1),
            timezone.now() + timedelta(days=365),
            2,
        ),
        (
            {"status": "EXPIRED"},
            timezone.now().replace(year=2015, month=1, day=1),
            timezone.now().replace(year=2018, month=1, day=1),
            1,
        ),
        (
            {"status": "SCHEDULED"},
            timezone.now() + timedelta(days=3),
            timezone.now() + timedelta(days=10),
            1,
        ),
    ],
)
def test_query_vouchers_with_filter_status(
    voucher_filter,
    start_date,
    end_date,
    count,
    staff_api_client,
    query_vouchers_with_filter,
    permission_manage_discounts,
):
    Voucher.objects.bulk_create(
        [
            Voucher(
                name="Voucher1",
                code="abc",
                start_date=timezone.now(),
            ),
            Voucher(
                name="Voucher2",
                code="123",
                start_date=start_date,
                end_date=end_date,
            ),
        ]
    )
    variables = {"filter": voucher_filter}
    response = staff_api_client.post_graphql(
        query_vouchers_with_filter, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["vouchers"]["edges"]
    assert len(data) == count


@pytest.mark.parametrize(
    "voucher_filter, count",
    [
        ({"timesUsed": {"gte": 1, "lte": 5}}, 1),
        ({"timesUsed": {"lte": 3}}, 2),
        ({"timesUsed": {"gte": 2}}, 1),
    ],
)
def test_query_vouchers_with_filter_times_used(
    voucher_filter,
    count,
    staff_api_client,
    query_vouchers_with_filter,
    permission_manage_discounts,
):
    Voucher.objects.bulk_create(
        [
            Voucher(name="Voucher1", code="abc"),
            Voucher(name="Voucher2", code="123", used=2),
        ]
    )
    variables = {"filter": voucher_filter}
    response = staff_api_client.post_graphql(
        query_vouchers_with_filter, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["vouchers"]["edges"]
    assert len(data) == count


@pytest.mark.parametrize(
    "voucher_filter, count",
    [
        ({"started": {"gte": "2019-04-18T00:00:00+00:00"}}, 1),
        ({"started": {"lte": "2012-01-14T00:00:00+00:00"}}, 1),
        (
            {
                "started": {
                    "lte": "2012-01-15T00:00:00+00:00",
                    "gte": "2012-01-01T00:00:00+00:00",
                }
            },
            1,
        ),
        ({"started": {"gte": "2012-01-03T00:00:00+00:00"}}, 2),
    ],
)
def test_query_vouchers_with_filter_started(
    voucher_filter,
    count,
    staff_api_client,
    query_vouchers_with_filter,
    permission_manage_discounts,
):
    Voucher.objects.bulk_create(
        [
            Voucher(name="Voucher1", code="abc"),
            Voucher(
                name="Voucher2",
                code="123",
                start_date=timezone.now().replace(year=2012, month=1, day=5),
            ),
        ]
    )
    variables = {"filter": voucher_filter}
    response = staff_api_client.post_graphql(
        query_vouchers_with_filter, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["vouchers"]["edges"]
    assert len(data) == count


@pytest.mark.parametrize(
    "voucher_filter, count, discount_value_type",
    [
        ({"discountType": "PERCENTAGE"}, 1, DiscountValueType.PERCENTAGE),
        ({"discountType": "FIXED"}, 2, DiscountValueType.FIXED),
    ],
)
def test_query_vouchers_with_filter_discount_type(
    voucher_filter,
    count,
    discount_value_type,
    staff_api_client,
    query_vouchers_with_filter,
    permission_manage_discounts,
):
    Voucher.objects.bulk_create(
        [
            Voucher(
                name="Voucher1",
                code="abc",
                discount_value_type=DiscountValueType.FIXED,
            ),
            Voucher(
                name="Voucher2",
                code="123",
                discount_value_type=discount_value_type,
            ),
        ]
    )
    variables = {"filter": voucher_filter}
    response = staff_api_client.post_graphql(
        query_vouchers_with_filter, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["vouchers"]["edges"]
    assert len(data) == count


@pytest.mark.parametrize(
    "voucher_filter, count", [({"search": "Big"}, 1), ({"search": "GIFT"}, 2)]
)
def test_query_vouchers_with_filter_search(
    voucher_filter,
    count,
    staff_api_client,
    query_vouchers_with_filter,
    permission_manage_discounts,
):
    Voucher.objects.bulk_create(
        [
            Voucher(name="The Biggest Voucher", code="GIFT"),
            Voucher(name="Voucher2", code="GIFT-COUPON"),
        ]
    )
    variables = {"filter": voucher_filter}
    response = staff_api_client.post_graphql(
        query_vouchers_with_filter, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["vouchers"]["edges"]
    assert len(data) == count


QUERY_VOUCHER_WITH_SORT = """
    query ($sort_by: VoucherSortingInput!) {
        vouchers(first:5, sortBy: $sort_by) {
            edges{
                node{
                    name
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "voucher_sort, result_order",
    [
        (
            {"field": "CODE", "direction": "ASC"},
            ["Voucher2", "Voucher1", "FreeShipping"],
        ),
        (
            {"field": "CODE", "direction": "DESC"},
            ["FreeShipping", "Voucher1", "Voucher2"],
        ),
        (
            {"field": "TYPE", "direction": "ASC"},
            ["Voucher1", "Voucher2", "FreeShipping"],
        ),
        (
            {"field": "TYPE", "direction": "DESC"},
            ["FreeShipping", "Voucher2", "Voucher1"],
        ),
        (
            {"field": "START_DATE", "direction": "ASC"},
            ["FreeShipping", "Voucher2", "Voucher1"],
        ),
        (
            {"field": "START_DATE", "direction": "DESC"},
            ["Voucher1", "Voucher2", "FreeShipping"],
        ),
        (
            {"field": "END_DATE", "direction": "ASC"},
            ["Voucher2", "FreeShipping", "Voucher1"],
        ),
        (
            {"field": "END_DATE", "direction": "DESC"},
            ["Voucher1", "FreeShipping", "Voucher2"],
        ),
        (
            {"field": "USAGE_LIMIT", "direction": "ASC"},
            ["Voucher1", "FreeShipping", "Voucher2"],
        ),
        (
            {"field": "USAGE_LIMIT", "direction": "DESC"},
            ["Voucher2", "FreeShipping", "Voucher1"],
        ),
    ],
)
def test_query_vouchers_with_sort(
    voucher_sort, result_order, staff_api_client, permission_manage_discounts
):
    Voucher.objects.bulk_create(
        [
            Voucher(
                name="Voucher1",
                code="abc",
                discount_value_type=DiscountValueType.FIXED,
                type=VoucherType.ENTIRE_ORDER,
                usage_limit=10,
            ),
            Voucher(
                name="Voucher2",
                code="123",
                discount_value_type=DiscountValueType.FIXED,
                type=VoucherType.ENTIRE_ORDER,
                start_date=timezone.now().replace(year=2012, month=1, day=5),
                end_date=timezone.now().replace(year=2013, month=1, day=5),
            ),
            Voucher(
                name="FreeShipping",
                code="xyz",
                discount_value_type=DiscountValueType.PERCENTAGE,
                type=VoucherType.SHIPPING,
                start_date=timezone.now().replace(year=2011, month=1, day=5),
                end_date=timezone.now().replace(year=2015, month=12, day=31),
                usage_limit=1000,
            ),
        ]
    )
    variables = {"sort_by": voucher_sort}
    staff_api_client.user.user_permissions.add(permission_manage_discounts)
    response = staff_api_client.post_graphql(QUERY_VOUCHER_WITH_SORT, variables)
    content = get_graphql_content(response)
    vouchers = content["data"]["vouchers"]["edges"]

    for order, voucher_name in enumerate(result_order):
        assert vouchers[order]["node"]["name"] == voucher_name


@pytest.mark.parametrize(
    "sale_filter, start_date, end_date, count",
    [
        (
            {"status": "ACTIVE"},
            timezone.now().replace(year=2015, month=1, day=1),
            timezone.now() + timedelta(days=365),
            2,
        ),
        (
            {"status": "EXPIRED"},
            timezone.now().replace(year=2015, month=1, day=1),
            timezone.now().replace(year=2018, month=1, day=1),
            1,
        ),
        (
            {"status": "SCHEDULED"},
            timezone.now() + timedelta(days=3),
            timezone.now() + timedelta(days=10),
            1,
        ),
    ],
)
def test_query_sales_with_filter_status(
    sale_filter,
    start_date,
    end_date,
    count,
    staff_api_client,
    query_sales_with_filter,
    permission_manage_discounts,
    channel_USD,
):
    sales = Sale.objects.bulk_create(
        [
            Sale(name="Sale1", start_date=timezone.now()),
            Sale(name="Sale2", start_date=start_date, end_date=end_date),
        ]
    )
    SaleChannelListing.objects.bulk_create(
        [
            SaleChannelListing(
                sale=sale,
                discount_value=123,
                channel=channel_USD,
                currency=channel_USD.currency_code,
            )
            for sale in sales
        ]
    )

    variables = {"filter": sale_filter}
    response = staff_api_client.post_graphql(
        query_sales_with_filter, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"]
    assert len(data) == count


@pytest.mark.parametrize(
    "sale_filter, count, sale_type",
    [
        ({"saleType": "PERCENTAGE"}, 1, DiscountValueType.PERCENTAGE),
        ({"saleType": "FIXED"}, 2, DiscountValueType.FIXED),
    ],
)
def test_query_sales_with_filter_discount_type(
    sale_filter,
    count,
    sale_type,
    staff_api_client,
    query_sales_with_filter,
    permission_manage_discounts,
):
    Sale.objects.bulk_create(
        [
            Sale(name="Sale1", type=DiscountValueType.FIXED),
            Sale(name="Sale2", type=sale_type),
        ]
    )
    variables = {"filter": sale_filter}
    response = staff_api_client.post_graphql(
        query_sales_with_filter, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"]
    assert len(data) == count


@pytest.mark.parametrize(
    "sale_filter, count",
    [
        ({"started": {"gte": "2019-04-18T00:00:00+00:00"}}, 1),
        ({"started": {"lte": "2012-01-14T00:00:00+00:00"}}, 1),
        (
            {
                "started": {
                    "lte": "2012-01-15T00:00:00+00:00",
                    "gte": "2012-01-01T00:00:00+00:00",
                }
            },
            1,
        ),
        ({"started": {"gte": "2012-01-03T00:00:00+00:00"}}, 2),
    ],
)
def test_query_sales_with_filter_started(
    sale_filter,
    count,
    staff_api_client,
    query_sales_with_filter,
    permission_manage_discounts,
    channel_USD,
):
    sales = Sale.objects.bulk_create(
        [
            Sale(name="Sale1"),
            Sale(
                name="Sale2",
                start_date=timezone.now().replace(year=2012, month=1, day=5),
            ),
        ]
    )
    SaleChannelListing.objects.bulk_create(
        [
            SaleChannelListing(
                sale=sale,
                discount_value=123,
                channel=channel_USD,
                currency=channel_USD.currency_code,
            )
            for sale in sales
        ]
    )

    variables = {"filter": sale_filter}
    response = staff_api_client.post_graphql(
        query_sales_with_filter, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"]
    assert len(data) == count


@pytest.mark.parametrize(
    "sale_filter, count",
    [
        ({"updatedAt": {"gte": "2012-01-14T10:59:00+00:00"}}, 2),
        ({"updatedAt": {"lte": "2012-01-14T12:00:05+00:00"}}, 2),
        ({"updatedAt": {"gte": "2012-01-14T11:59:00+00:00"}}, 1),
        ({"updatedAt": {"lte": "2012-01-14T11:05:00+00:00"}}, 1),
        ({"updatedAt": {"gte": "2012-01-14T12:01:00+00:00"}}, 0),
        ({"updatedAt": {"lte": "2012-01-14T10:59:00+00:00"}}, 0),
        (
            {
                "updatedAt": {
                    "lte": "2012-01-14T12:01:00+00:00",
                    "gte": "2012-01-14T11:59:00+00:00",
                },
            },
            1,
        ),
    ],
)
def test_query_sales_with_filter_updated_at(
    sale_filter,
    count,
    staff_api_client,
    query_sales_with_filter,
    permission_manage_discounts,
    channel_USD,
):
    with freeze_time("2012-01-14 11:00:00"):
        sale_1 = Sale.objects.create(name="Sale1")

    with freeze_time("2012-01-14 12:00:00"):
        sale_2 = Sale.objects.create(name="Sale2")

    SaleChannelListing.objects.bulk_create(
        [
            SaleChannelListing(
                sale=sale,
                discount_value=123,
                channel=channel_USD,
                currency=channel_USD.currency_code,
            )
            for sale in [sale_1, sale_2]
        ]
    )

    variables = {"filter": sale_filter}
    response = staff_api_client.post_graphql(
        query_sales_with_filter, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"]
    assert len(data) == count


@pytest.mark.parametrize(
    "sale_filter, count",
    [({"search": "Big"}, 1), ({"search": "69"}, 1), ({"search": "FIX"}, 2)],
)
def test_query_sales_with_filter_search(
    sale_filter,
    count,
    staff_api_client,
    query_sales_with_filter,
    permission_manage_discounts,
    channel_USD,
):
    sales = Sale.objects.bulk_create(
        [
            Sale(name="BigSale", type="PERCENTAGE"),
            Sale(
                name="Sale2",
                type="FIXED",
                start_date=timezone.now().replace(year=2012, month=1, day=5),
            ),
            Sale(
                name="Sale3",
                type="FIXED",
                start_date=timezone.now().replace(year=2012, month=1, day=5),
            ),
        ]
    )
    values = [123, 123, 69]
    SaleChannelListing.objects.bulk_create(
        [
            SaleChannelListing(channel=channel_USD, discount_value=values[i], sale=sale)
            for i, sale in enumerate(sales)
        ]
    )
    variables = {"filter": sale_filter}
    response = staff_api_client.post_graphql(
        query_sales_with_filter, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"]
    assert len(data) == count


QUERY_SALE_WITH_SORT = """
    query ($sort_by: SaleSortingInput!) {
        sales(first:5, sortBy: $sort_by) {
            edges{
                node{
                    name
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "sale_sort, result_order",
    [
        ({"field": "NAME", "direction": "ASC"}, ["BigSale", "Sale2", "Sale3"]),
        ({"field": "NAME", "direction": "DESC"}, ["Sale3", "Sale2", "BigSale"]),
        ({"field": "TYPE", "direction": "ASC"}, ["Sale2", "Sale3", "BigSale"]),
        ({"field": "TYPE", "direction": "DESC"}, ["BigSale", "Sale3", "Sale2"]),
        ({"field": "START_DATE", "direction": "ASC"}, ["Sale3", "Sale2", "BigSale"]),
        ({"field": "START_DATE", "direction": "DESC"}, ["BigSale", "Sale2", "Sale3"]),
        ({"field": "END_DATE", "direction": "ASC"}, ["Sale2", "Sale3", "BigSale"]),
        ({"field": "END_DATE", "direction": "DESC"}, ["BigSale", "Sale3", "Sale2"]),
    ],
)
def test_query_sales_with_sort(
    sale_sort, result_order, staff_api_client, permission_manage_discounts, channel_USD
):
    sales = Sale.objects.bulk_create(
        [
            Sale(name="BigSale", type="PERCENTAGE"),
            Sale(
                name="Sale2",
                type="FIXED",
                start_date=timezone.now().replace(year=2012, month=1, day=5),
                end_date=timezone.now().replace(year=2013, month=1, day=5),
            ),
            Sale(
                name="Sale3",
                type="FIXED",
                start_date=timezone.now().replace(year=2011, month=1, day=5),
                end_date=timezone.now().replace(year=2015, month=12, day=31),
            ),
        ]
    )
    variables = {"sort_by": sale_sort}
    staff_api_client.user.user_permissions.add(permission_manage_discounts)
    response = staff_api_client.post_graphql(QUERY_SALE_WITH_SORT, variables)
    content = get_graphql_content(response)
    sales = content["data"]["sales"]["edges"]

    for order, sale_name in enumerate(result_order):
        assert sales[order]["node"]["name"] == sale_name


QUERY_SALE_BY_ID = """
    query Sale($id: ID!) {
        sale(id: $id) {
            id
            name
            type
            discountValue
        }
    }
"""


def test_staff_query_sale(staff_api_client, sale, permission_manage_discounts):
    variables = {"id": graphene.Node.to_global_id("Sale", sale.pk)}
    response = staff_api_client.post_graphql(
        QUERY_SALE_BY_ID, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    assert content["data"]["sale"]["name"] == sale.name
    assert content["data"]["sale"]["type"] == sale.type.upper()


def test_query_sale_by_app(app_api_client, sale, permission_manage_discounts):
    variables = {"id": graphene.Node.to_global_id("Sale", sale.pk)}
    response = app_api_client.post_graphql(
        QUERY_SALE_BY_ID, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    assert content["data"]["sale"]["name"] == sale.name
    assert content["data"]["sale"]["type"] == sale.type.upper()


def test_query_sale_by_customer(api_client, sale, permission_manage_discounts):
    variables = {"id": graphene.Node.to_global_id("Sale", sale.pk)}
    response = api_client.post_graphql(QUERY_SALE_BY_ID, variables)
    assert_no_permission(response)


def test_staff_query_sale_by_invalid_id(
    staff_api_client, sale, permission_manage_discounts
):
    id = "bh/"
    variables = {"id": id}
    response = staff_api_client.post_graphql(
        QUERY_SALE_BY_ID, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {id}."
    assert content["data"]["sale"] is None


def test_staff_query_sale_with_invalid_object_type(
    staff_api_client, sale, permission_manage_discounts
):
    variables = {"id": graphene.Node.to_global_id("Order", sale.pk)}
    response = staff_api_client.post_graphql(
        QUERY_SALE_BY_ID, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    assert content["data"]["sale"] is None


QUERY_VOUCHER_BY_ID = """
    query Voucher($id: ID!) {
        voucher(id: $id) {
            id
            code
            name
            discountValue
        }
    }
"""


def test_staff_query_voucher(staff_api_client, voucher, permission_manage_discounts):
    variables = {"id": graphene.Node.to_global_id("Voucher", voucher.pk)}
    response = staff_api_client.post_graphql(
        QUERY_VOUCHER_BY_ID, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    assert content["data"]["voucher"]["name"] == voucher.name
    assert content["data"]["voucher"]["code"] == voucher.code


def test_query_voucher_by_app(app_api_client, voucher, permission_manage_discounts):
    variables = {"id": graphene.Node.to_global_id("Voucher", voucher.pk)}
    response = app_api_client.post_graphql(
        QUERY_VOUCHER_BY_ID, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    assert content["data"]["voucher"]["name"] == voucher.name
    assert content["data"]["voucher"]["code"] == voucher.code


def test_query_voucher_by_customer(api_client, voucher, permission_manage_discounts):
    variables = {"id": graphene.Node.to_global_id("Voucher", voucher.pk)}
    response = api_client.post_graphql(QUERY_VOUCHER_BY_ID, variables)
    assert_no_permission(response)


def test_staff_query_voucher_by_invalid_id(
    staff_api_client, voucher, permission_manage_discounts
):
    id = "bh/"
    variables = {"id": id}
    response = staff_api_client.post_graphql(
        QUERY_VOUCHER_BY_ID, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {id}."
    assert content["data"]["voucher"] is None


def test_staff_query_voucher_with_invalid_object_type(
    staff_api_client, voucher, permission_manage_discounts
):
    variables = {"id": graphene.Node.to_global_id("Order", voucher.pk)}
    response = staff_api_client.post_graphql(
        QUERY_VOUCHER_BY_ID, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    assert content["data"]["voucher"] is None

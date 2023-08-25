import json
from datetime import timedelta
from unittest import mock

import graphene
import pytest
from django.utils.functional import SimpleLazyObject
from django.utils.text import slugify
from freezegun import freeze_time

from .....channel.error_codes import ChannelErrorCode
from .....channel.models import Channel
from .....core.utils.json_serializer import CustomJsonEncoder
from .....tax.models import TaxConfiguration
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import (
    AllocationStrategyEnum,
    MarkAsPaidStrategyEnum,
    TransactionFlowStrategyEnum,
)

CHANNEL_CREATE_MUTATION = """
    mutation CreateChannel($input: ChannelCreateInput!){
        channelCreate(input: $input){
            channel{
                id
                name
                slug
                currencyCode
                defaultCountry {
                    code
                    country
                }
                warehouses {
                    slug
                }
                stockSettings {
                    allocationStrategy
                }
                orderSettings {
                    automaticallyConfirmAllNewOrders
                    automaticallyFulfillNonShippableGiftCard
                    expireOrdersAfter
                    markAsPaidStrategy
                    defaultTransactionFlowStrategy
                    deleteExpiredOrdersAfter
                    allowUnpaidOrders
                }
                checkoutSettings {
                    useLegacyErrorFlow
                }
                paymentSettings {
                    defaultTransactionFlowStrategy
                }
            }
            errors{
                field
                code
                message
            }
        }
    }
"""


def test_channel_create_mutation_as_staff_user(
    permission_manage_channels,
    staff_api_client,
):
    # given
    name = "testName"
    slug = "test_slug"
    currency_code = "USD"
    default_country = "US"
    allocation_strategy = AllocationStrategyEnum.PRIORITIZE_HIGH_STOCK.name
    variables = {
        "input": {
            "name": name,
            "slug": slug,
            "currencyCode": currency_code,
            "defaultCountry": default_country,
            "stockSettings": {"allocationStrategy": allocation_strategy},
            "orderSettings": {
                "automaticallyConfirmAllNewOrders": False,
                "automaticallyFulfillNonShippableGiftCard": False,
                "expireOrdersAfter": 10,
            },
            "checkoutSettings": {"useLegacyErrorFlow": False},
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelCreate"]
    assert not data["errors"]
    channel_data = data["channel"]
    channel = Channel.objects.get()
    assert channel_data["name"] == channel.name == name
    assert channel_data["slug"] == channel.slug == slug
    assert channel_data["currencyCode"] == channel.currency_code == currency_code
    assert (
        channel_data["defaultCountry"]["code"]
        == channel.default_country.code
        == default_country
    )
    assert channel_data["stockSettings"]["allocationStrategy"] == allocation_strategy
    assert channel_data["orderSettings"]["automaticallyConfirmAllNewOrders"] is False
    assert (
        channel_data["orderSettings"]["automaticallyFulfillNonShippableGiftCard"]
        is False
    )
    assert channel_data["orderSettings"]["expireOrdersAfter"] == 10
    assert channel_data["checkoutSettings"]["useLegacyErrorFlow"] is False


def test_channel_create_mutation_as_app(
    permission_manage_channels,
    app_api_client,
):
    # given
    name = "testName"
    slug = "test_slug"
    currency_code = "USD"
    default_country = "US"
    variables = {
        "input": {
            "name": name,
            "slug": slug,
            "currencyCode": currency_code,
            "defaultCountry": default_country,
            "checkoutSettings": {"useLegacyErrorFlow": False},
        }
    }

    # when
    response = app_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelCreate"]
    assert not data["errors"]
    channel_data = data["channel"]
    channel = Channel.objects.get()
    assert channel_data["name"] == channel.name == name
    assert channel_data["slug"] == channel.slug == slug
    assert channel_data["currencyCode"] == channel.currency_code == currency_code
    assert (
        channel_data["defaultCountry"]["code"]
        == channel.default_country.code
        == default_country
    )
    assert (
        channel_data["stockSettings"]["allocationStrategy"]
        == AllocationStrategyEnum.PRIORITIZE_SORTING_ORDER.name
    )
    assert channel_data["orderSettings"]["automaticallyConfirmAllNewOrders"] is True
    assert (
        channel_data["orderSettings"]["automaticallyFulfillNonShippableGiftCard"]
        is True
    )
    assert channel_data["orderSettings"]["expireOrdersAfter"] is None
    assert channel_data["checkoutSettings"]["useLegacyErrorFlow"] is False


def test_channel_create_mutation_as_customer(user_api_client):
    # given
    name = "testName"
    slug = "test_slug"
    currency_code = "USD"
    default_country = "US"
    allocation_strategy = AllocationStrategyEnum.PRIORITIZE_SORTING_ORDER.name
    variables = {
        "input": {
            "name": name,
            "slug": slug,
            "currencyCode": currency_code,
            "defaultCountry": default_country,
            "stockSettings": {"allocationStrategy": allocation_strategy},
            "orderSettings": {
                "automaticallyConfirmAllNewOrders": False,
                "automaticallyFulfillNonShippableGiftCard": False,
            },
        }
    }

    # when
    response = user_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(),
    )

    # then
    assert_no_permission(response)


def test_channel_create_mutation_negative_expire_orders(
    permission_manage_channels,
    app_api_client,
):
    # given
    name = "testName"
    slug = "test_slug"
    currency_code = "USD"
    default_country = "US"
    allocation_strategy = AllocationStrategyEnum.PRIORITIZE_SORTING_ORDER.name
    variables = {
        "input": {
            "name": name,
            "slug": slug,
            "currencyCode": currency_code,
            "defaultCountry": default_country,
            "stockSettings": {"allocationStrategy": allocation_strategy},
            "orderSettings": {
                "expireOrdersAfter": -1,
            },
        }
    }

    # when
    response = app_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )

    # then
    content = get_graphql_content(response)
    error = content["data"]["channelCreate"]["errors"][0]
    assert error["field"] == "expireOrdersAfter"
    assert error["code"] == ChannelErrorCode.INVALID.name


@pytest.mark.parametrize("expire_input", [0, None])
def test_channel_create_mutation_disabled_expire_orders(
    expire_input,
    permission_manage_channels,
    app_api_client,
):
    # given
    name = "testName"
    slug = "test_slug"
    currency_code = "USD"
    default_country = "US"
    allocation_strategy = AllocationStrategyEnum.PRIORITIZE_SORTING_ORDER.name
    variables = {
        "input": {
            "name": name,
            "slug": slug,
            "currencyCode": currency_code,
            "defaultCountry": default_country,
            "stockSettings": {"allocationStrategy": allocation_strategy},
            "orderSettings": {
                "expireOrdersAfter": expire_input,
            },
        }
    }

    # when
    response = app_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["channelCreate"]
    assert not data["errors"]
    assert data["channel"]["orderSettings"]["expireOrdersAfter"] is None


def test_channel_create_mutation_as_anonymous(api_client):
    # given
    name = "testName"
    slug = "test_slug"
    currency_code = "USD"
    default_country = "US"
    variables = {
        "input": {
            "name": name,
            "slug": slug,
            "currencyCode": currency_code,
            "defaultCountry": default_country,
        }
    }

    # when
    response = api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(),
    )

    # then
    assert_no_permission(response)


def test_channel_create_mutation_slugify_slug_field(
    permission_manage_channels,
    staff_api_client,
):
    # given
    name = "testName"
    slug = "Invalid slug"
    currency_code = "USD"
    default_country = "US"
    variables = {
        "input": {
            "name": name,
            "slug": slug,
            "currencyCode": currency_code,
            "defaultCountry": default_country,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    channel_data = content["data"]["channelCreate"]["channel"]
    assert channel_data["slug"] == slugify(slug)


def test_channel_create_mutation_with_duplicated_slug(
    permission_manage_channels, staff_api_client, channel_USD
):
    # given
    name = "New Channel"
    slug = channel_USD.slug
    currency_code = "USD"
    default_country = "US"
    allocation_strategy = AllocationStrategyEnum.PRIORITIZE_SORTING_ORDER.name
    variables = {
        "input": {
            "name": name,
            "slug": slug,
            "currencyCode": currency_code,
            "defaultCountry": default_country,
            "stockSettings": {"allocationStrategy": allocation_strategy},
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    error = content["data"]["channelCreate"]["errors"][0]
    assert error["field"] == "slug"
    assert error["code"] == ChannelErrorCode.UNIQUE.name


def test_channel_create_mutation_with_shipping_zones(
    permission_manage_channels,
    staff_api_client,
    shipping_zones,
):
    # given
    name = "testName"
    slug = "test_slug"
    currency_code = "USD"
    default_country = "US"
    shipping_zones_ids = [
        graphene.Node.to_global_id("ShippingZone", zone.pk) for zone in shipping_zones
    ]
    allocation_strategy = AllocationStrategyEnum.PRIORITIZE_SORTING_ORDER.name
    variables = {
        "input": {
            "name": name,
            "slug": slug,
            "currencyCode": currency_code,
            "addShippingZones": shipping_zones_ids,
            "defaultCountry": default_country,
            "stockSettings": {"allocationStrategy": allocation_strategy},
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelCreate"]
    assert not data["errors"]
    channel_data = data["channel"]
    channel = Channel.objects.get(
        id=graphene.Node.from_global_id(channel_data["id"])[1]
    )
    assert channel_data["name"] == channel.name == name
    assert channel_data["slug"] == channel.slug == slug
    assert channel_data["currencyCode"] == channel.currency_code == currency_code
    for shipping_zone in shipping_zones:
        shipping_zone.channels.get(slug=slug)
    assert channel_data["stockSettings"]["allocationStrategy"] == allocation_strategy


def test_channel_create_mutation_with_warehouses(
    permission_manage_channels,
    staff_api_client,
    warehouses,
):
    # given
    name = "testName"
    slug = "test_slug"
    currency_code = "USD"
    default_country = "US"
    warehouses_ids = [
        graphene.Node.to_global_id("Warehouse", warehouse.pk)
        for warehouse in warehouses
    ]
    allocation_strategy = AllocationStrategyEnum.PRIORITIZE_SORTING_ORDER.name
    variables = {
        "input": {
            "name": name,
            "slug": slug,
            "currencyCode": currency_code,
            "addWarehouses": warehouses_ids,
            "defaultCountry": default_country,
            "stockSettings": {"allocationStrategy": allocation_strategy},
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelCreate"]
    assert not data["errors"]
    channel_data = data["channel"]
    channel = Channel.objects.get(
        id=graphene.Node.from_global_id(channel_data["id"])[1]
    )
    assert channel_data["name"] == channel.name == name
    assert channel_data["slug"] == channel.slug == slug
    assert channel_data["currencyCode"] == channel.currency_code == currency_code
    assert {
        warehouse_data["slug"] for warehouse_data in channel_data["warehouses"]
    } == {warehouse.slug for warehouse in warehouses}
    assert channel_data["stockSettings"]["allocationStrategy"] == allocation_strategy


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_channel_create_mutation_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    permission_manage_channels,
    staff_api_client,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    name = "testName"
    slug = "test_slug"
    currency_code = "USD"
    default_country = "US"
    allocation_strategy = AllocationStrategyEnum.PRIORITIZE_SORTING_ORDER.name
    variables = {
        "input": {
            "name": name,
            "slug": slug,
            "currencyCode": currency_code,
            "defaultCountry": default_country,
            "stockSettings": {"allocationStrategy": allocation_strategy},
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)
    channel = Channel.objects.last()
    data = content["data"]["channelCreate"]

    # then
    assert data["channel"]
    assert not data["errors"]

    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": graphene.Node.to_global_id("Channel", channel.id),
                "is_active": channel.is_active,
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.CHANNEL_CREATED,
        [any_webhook],
        channel,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_channel_create_creates_tax_configuration(
    permission_manage_channels, staff_api_client
):
    # given
    slug = "channel-with-tax-config"
    variables = {
        "input": {
            "name": "Channel with tax config",
            "slug": slug,
            "currencyCode": "USD",
            "defaultCountry": "US",
        }
    }

    # when
    staff_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )

    # then
    channel = Channel.objects.get(slug=slug)
    assert TaxConfiguration.objects.filter(channel=channel).exists()


def test_channel_create_set_order_mark_as_paid(
    permission_manage_channels,
    staff_api_client,
):
    # given
    name = "testName"
    slug = "test_slug"
    currency_code = "USD"
    default_country = "US"
    variables = {
        "input": {
            "name": name,
            "slug": slug,
            "currencyCode": currency_code,
            "defaultCountry": default_country,
            "orderSettings": {
                "markAsPaidStrategy": MarkAsPaidStrategyEnum.TRANSACTION_FLOW.name
            },
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelCreate"]
    assert not data["errors"]
    channel_data = data["channel"]
    channel = Channel.objects.get()
    assert (
        channel_data["orderSettings"]["markAsPaidStrategy"]
        == MarkAsPaidStrategyEnum.TRANSACTION_FLOW.name
    )
    assert (
        channel.order_mark_as_paid_strategy
        == MarkAsPaidStrategyEnum.TRANSACTION_FLOW.value
    )


def test_channel_create_set_default_transaction_flow_strategy_via_order_settings(
    permission_manage_channels,
    staff_api_client,
):
    # given
    name = "testName"
    slug = "test_slug"
    currency_code = "USD"
    default_country = "US"
    variables = {
        "input": {
            "name": name,
            "slug": slug,
            "currencyCode": currency_code,
            "defaultCountry": default_country,
            "orderSettings": {
                "defaultTransactionFlowStrategy": (
                    TransactionFlowStrategyEnum.AUTHORIZATION.name
                )
            },
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelCreate"]
    assert not data["errors"]
    channel_data = data["channel"]
    channel = Channel.objects.get()
    assert (
        channel_data["orderSettings"]["defaultTransactionFlowStrategy"]
        == TransactionFlowStrategyEnum.AUTHORIZATION.name
    )
    assert (
        channel.default_transaction_flow_strategy
        == TransactionFlowStrategyEnum.AUTHORIZATION.value
    )


def test_channel_create_set_default_transaction_flow_strategy(
    permission_manage_channels,
    staff_api_client,
):
    # given
    name = "testName"
    slug = "test_slug"
    currency_code = "USD"
    default_country = "US"
    variables = {
        "input": {
            "name": name,
            "slug": slug,
            "currencyCode": currency_code,
            "defaultCountry": default_country,
            "paymentSettings": {
                "defaultTransactionFlowStrategy": (
                    TransactionFlowStrategyEnum.AUTHORIZATION.name
                )
            },
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelCreate"]
    assert not data["errors"]
    channel_data = data["channel"]
    channel = Channel.objects.get()
    assert (
        channel_data["paymentSettings"]["defaultTransactionFlowStrategy"]
        == TransactionFlowStrategyEnum.AUTHORIZATION.name
    )
    assert (
        channel.default_transaction_flow_strategy
        == TransactionFlowStrategyEnum.AUTHORIZATION.value
    )


def test_channel_create_set_delete_expired_orders_after(
    permission_manage_channels,
    staff_api_client,
):
    # given
    name = "testName"
    slug = "test_slug"
    currency_code = "USD"
    default_country = "US"
    delete_expired_after = 10
    variables = {
        "input": {
            "name": name,
            "slug": slug,
            "currencyCode": currency_code,
            "defaultCountry": default_country,
            "orderSettings": {"deleteExpiredOrdersAfter": delete_expired_after},
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelCreate"]
    assert not data["errors"]
    channel_data = data["channel"]
    channel = Channel.objects.get()
    assert (
        channel_data["orderSettings"]["deleteExpiredOrdersAfter"]
        == delete_expired_after
    )
    assert channel.delete_expired_orders_after == timedelta(days=delete_expired_after)


@pytest.mark.parametrize("delete_expired_after", [-1, 0, 121, 300])
def test_channel_create_mutation_set_incorrect_delete_expired_orders_after(
    delete_expired_after, permission_manage_channels, staff_api_client, channel_USD
):
    # given
    name = "testName"
    slug = "test_slug"
    currency_code = "USD"
    default_country = "US"
    variables = {
        "input": {
            "name": name,
            "slug": slug,
            "currencyCode": currency_code,
            "defaultCountry": default_country,
            "orderSettings": {"deleteExpiredOrdersAfter": delete_expired_after},
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    error = content["data"]["channelCreate"]["errors"][0]
    assert error["field"] == "deleteExpiredOrdersAfter"
    assert error["code"] == ChannelErrorCode.INVALID.name


def test_channel_create_set_checkout_use_legacy_error_flow(
    permission_manage_channels,
    staff_api_client,
):
    # given
    name = "testName"
    slug = "test_slug"
    currency_code = "USD"
    default_country = "US"
    variables = {
        "input": {
            "name": name,
            "slug": slug,
            "currencyCode": currency_code,
            "defaultCountry": default_country,
            "checkoutSettings": {"useLegacyErrorFlow": False},
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelCreate"]
    assert not data["errors"]
    channel_data = data["channel"]
    channel = Channel.objects.get()
    assert channel_data["checkoutSettings"]["useLegacyErrorFlow"] is False
    assert channel.use_legacy_error_flow_for_checkout is False


@pytest.mark.parametrize("allowUnpaid", [True, False])
def test_channel_create_set_allow_unpaid_orders(
    allowUnpaid,
    permission_manage_channels,
    staff_api_client,
):
    # given
    name = "testName"
    slug = "test_slug"
    currency_code = "USD"
    default_country = "US"
    variables = {
        "input": {
            "name": name,
            "slug": slug,
            "currencyCode": currency_code,
            "defaultCountry": default_country,
            "orderSettings": {"allowUnpaidOrders": allowUnpaid},
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelCreate"]
    assert not data["errors"]
    channel_data = data["channel"]
    channel = Channel.objects.get()
    assert channel_data["orderSettings"]["allowUnpaidOrders"] == allowUnpaid
    assert channel.allow_unpaid_orders == allowUnpaid

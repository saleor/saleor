import json
from unittest.mock import patch

import graphene
import pytest
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....discount import DiscountValueType
from .....discount.error_codes import DiscountErrorCode
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

VOUCHER_CHANNEL_LISTING_UPDATE_MUTATION = """
mutation UpdateVoucherChannelListing($id: ID!, $input: VoucherChannelListingInput!) {
    voucherChannelListingUpdate(id: $id, input: $input) {
        errors {
            field
            message
            code
            channels
        }
        voucher {
            code
            channelListings {
                channel{
                    slug
                }
                discountValue
                currency
                minSpent {
                    currency
                    amount
                }
            }
        }
    }
}
"""


def test_voucher_channel_listing_create_as_staff(
    staff_api_client, voucher_without_channel, permission_manage_discounts, channel_USD
):
    # given
    voucher = voucher_without_channel
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    discount_value = 5.5
    variables = {
        "id": voucher_id,
        "input": {
            "addChannels": [{"channelId": channel_id, "discountValue": discount_value}]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["voucherChannelListingUpdate"]["voucher"]
    assert not content["data"]["voucherChannelListingUpdate"]["errors"]
    channel_listing = data["channelListings"]
    assert channel_listing[0]["channel"]["slug"] == channel_USD.slug
    assert channel_listing[0]["discountValue"] == discount_value
    assert channel_listing[0]["currency"] == channel_USD.currency_code


def test_voucher_channel_listing_update_as_app(
    app_api_client, voucher_without_channel, permission_manage_discounts, channel_USD
):
    # given
    voucher = voucher_without_channel
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    discount_value = 5.5
    variables = {
        "id": voucher_id,
        "input": {
            "addChannels": [{"channelId": channel_id, "discountValue": discount_value}]
        },
    }

    # when
    response = app_api_client.post_graphql(
        VOUCHER_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["voucherChannelListingUpdate"]["voucher"]
    assert not content["data"]["voucherChannelListingUpdate"]["errors"]
    channel_listing = data["channelListings"]
    assert channel_listing[0]["channel"]["slug"] == channel_USD.slug
    assert channel_listing[0]["discountValue"] == discount_value
    assert channel_listing[0]["currency"] == channel_USD.currency_code


def test_voucher_channel_listing_update_as_customer(
    user_api_client, voucher_without_channel, channel_USD
):
    # given
    voucher = voucher_without_channel
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": voucher_id,
        "input": {"addChannels": [{"channelId": channel_id, "discountValue": 5.5}]},
    }

    # when
    response = user_api_client.post_graphql(
        VOUCHER_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
    )

    # then
    assert_no_permission(response)


@freeze_time("2022-05-12 12:00:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_voucher_channel_listing_update_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    permission_manage_discounts,
    staff_api_client,
    voucher_without_channel,
    channel_USD,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    voucher = voucher_without_channel
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": voucher_id,
        "input": {"addChannels": [{"channelId": channel_id, "discountValue": 5.5}]},
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["voucherChannelListingUpdate"]["voucher"]
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
        allow_replica=False,
    )


def test_voucher_channel_listing_update_as_anonymous(
    api_client, voucher_without_channel, channel_USD
):
    # given
    voucher = voucher_without_channel
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": voucher_id,
        "input": {"addChannels": [{"channelId": channel_id, "discountValue": 5.5}]},
    }

    # when
    response = api_client.post_graphql(
        VOUCHER_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
    )

    # then
    assert_no_permission(response)


def test_voucher_channel_listing_create_many_channel(
    staff_api_client,
    voucher_without_channel,
    permission_manage_discounts,
    channel_USD,
    channel_PLN,
):
    # given
    voucher = voucher_without_channel
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    channel_pln_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    discount_value = 5.5
    discount_value_pln = 50.5
    min_amount_spent = 10.1
    min_amount_spent_pln = 100.2
    variables = {
        "id": voucher_id,
        "input": {
            "addChannels": [
                {
                    "channelId": channel_id,
                    "discountValue": discount_value,
                    "minAmountSpent": min_amount_spent,
                },
                {
                    "channelId": channel_pln_id,
                    "discountValue": discount_value_pln,
                    "minAmountSpent": min_amount_spent_pln,
                },
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["voucherChannelListingUpdate"]["voucher"]
    assert not content["data"]["voucherChannelListingUpdate"]["errors"]
    channel_listing = data["channelListings"]
    assert channel_listing[0]["channel"]["slug"] == channel_USD.slug
    assert channel_listing[0]["discountValue"] == discount_value
    assert channel_listing[0]["minSpent"]["amount"] == min_amount_spent
    assert channel_listing[0]["currency"] == channel_USD.currency_code
    assert channel_listing[1]["channel"]["slug"] == channel_PLN.slug
    assert channel_listing[1]["discountValue"] == discount_value_pln
    assert channel_listing[1]["minSpent"]["amount"] == min_amount_spent_pln
    assert channel_listing[1]["currency"] == channel_PLN.currency_code


def test_voucher_channel_listing_create_and_remove(
    staff_api_client,
    voucher,
    permission_manage_discounts,
    channel_USD,
    channel_PLN,
):
    # given
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    channel_pln_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    discount_value_pln = 50.5
    min_amount_spent_pln = 100.2
    variables = {
        "id": voucher_id,
        "input": {
            "addChannels": [
                {
                    "channelId": channel_pln_id,
                    "discountValue": discount_value_pln,
                    "minAmountSpent": min_amount_spent_pln,
                }
            ],
            "removeChannels": [channel_id],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["voucherChannelListingUpdate"]["voucher"]
    assert not content["data"]["voucherChannelListingUpdate"]["errors"]
    channel_listing = data["channelListings"]
    assert len(channel_listing) == 1
    assert channel_listing[0]["channel"]["slug"] == channel_PLN.slug
    assert channel_listing[0]["discountValue"] == discount_value_pln
    assert channel_listing[0]["minSpent"]["amount"] == min_amount_spent_pln
    assert channel_listing[0]["currency"] == channel_PLN.currency_code


def test_voucher_channel_listing_update(
    staff_api_client,
    voucher,
    permission_manage_discounts,
    channel_USD,
):
    # given
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    discount_value = 5.5
    min_amount_spent = 100.2
    assert not voucher.channel_listings.get().discount_value == discount_value
    variables = {
        "id": voucher_id,
        "input": {
            "addChannels": [
                {
                    "channelId": channel_id,
                    "discountValue": discount_value,
                    "minAmountSpent": min_amount_spent,
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["voucherChannelListingUpdate"]["voucher"]
    assert not content["data"]["voucherChannelListingUpdate"]["errors"]
    channel_listing = data["channelListings"]
    assert len(channel_listing) == 1
    assert channel_listing[0]["channel"]["slug"] == channel_USD.slug
    assert channel_listing[0]["discountValue"] == discount_value
    assert channel_listing[0]["minSpent"]["amount"] == min_amount_spent
    assert channel_listing[0]["currency"] == channel_USD.currency_code


def test_voucher_channel_listing_update_without_discount_value(
    staff_api_client,
    voucher,
    permission_manage_discounts,
    channel_USD,
):
    # given
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    min_amount_spent = 100.2
    variables = {
        "id": voucher_id,
        "input": {
            "addChannels": [
                {"channelId": channel_id, "minAmountSpent": min_amount_spent}
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["voucherChannelListingUpdate"]["voucher"]
    assert not content["data"]["voucherChannelListingUpdate"]["errors"]
    channel_listing = data["channelListings"]
    assert len(channel_listing) == 1
    assert channel_listing[0]["channel"]["slug"] == channel_USD.slug
    assert channel_listing[0]["discountValue"] == 20
    assert channel_listing[0]["minSpent"]["amount"] == min_amount_spent
    assert channel_listing[0]["currency"] == channel_USD.currency_code


def test_voucher_channel_listing_remove_channel(
    staff_api_client,
    voucher,
    permission_manage_discounts,
    channel_USD,
):
    # given
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": voucher_id,
        "input": {"removeChannels": [channel_id]},
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["voucherChannelListingUpdate"]["voucher"]
    assert not content["data"]["voucherChannelListingUpdate"]["errors"]
    channel_listing = data["channelListings"]
    assert len(channel_listing) == 0


def test_voucher_channel_listing_update_with_null_as_discount_value(
    staff_api_client,
    voucher,
    permission_manage_discounts,
    channel_USD,
):
    # given
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": voucher_id,
        "input": {
            "addChannels": [
                {
                    "channelId": channel_id,
                    "discountValue": None,
                    "minAmountSpent": 100.2,
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["voucherChannelListingUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "discountValue"
    assert errors[0]["code"] == DiscountErrorCode.REQUIRED.name
    assert errors[0]["channels"] == [channel_id]


def test_voucher_channel_listing_create_with_null_as_discount_value(
    staff_api_client,
    voucher_without_channel,
    permission_manage_discounts,
    channel_USD,
):
    # given
    voucher = voucher_without_channel
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": voucher_id,
        "input": {
            "addChannels": [
                {
                    "channelId": channel_id,
                    "discountValue": None,
                    "minAmountSpent": 100.2,
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["voucherChannelListingUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "discountValue"
    assert errors[0]["code"] == DiscountErrorCode.REQUIRED.name
    assert errors[0]["channels"] == [channel_id]


def test_voucher_channel_listing_create_with_invalid_percentage_value(
    staff_api_client,
    voucher_without_channel,
    permission_manage_discounts,
    channel_USD,
):
    # given
    voucher = voucher_without_channel
    voucher.discount_value_type = DiscountValueType.PERCENTAGE
    voucher.save()
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": voucher_id,
        "input": {
            "addChannels": [
                {
                    "channelId": channel_id,
                    "discountValue": 101,
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["voucherChannelListingUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "discountValue"
    assert errors[0]["code"] == DiscountErrorCode.INVALID.name
    assert errors[0]["channels"] == [channel_id]


def test_voucher_channel_listing_create_without_discount_value(
    staff_api_client,
    voucher_without_channel,
    permission_manage_discounts,
    channel_USD,
):
    # given
    voucher = voucher_without_channel
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": voucher_id,
        "input": {"addChannels": [{"channelId": channel_id, "minAmountSpent": 100.2}]},
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["voucherChannelListingUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "discountValue"
    assert errors[0]["code"] == DiscountErrorCode.REQUIRED.name
    assert errors[0]["channels"] == [channel_id]


def test_voucher_channel_listing_update_duplicates_in_add(
    staff_api_client,
    voucher,
    permission_manage_discounts,
    channel_USD,
):
    # given
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": voucher_id,
        "input": {
            "addChannels": [
                {"channelId": channel_id, "discountValue": 50.5},
                {"channelId": channel_id, "discountValue": 50.5},
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["voucherChannelListingUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "addChannels"
    assert errors[0]["code"] == DiscountErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["channels"] == [channel_id]


def test_voucher_channel_listing_update_duplicates_in_remove(
    staff_api_client,
    voucher,
    permission_manage_discounts,
    channel_USD,
):
    # given
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": voucher_id,
        "input": {"removeChannels": [channel_id, channel_id]},
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["voucherChannelListingUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "removeChannels"
    assert errors[0]["code"] == DiscountErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["channels"] == [channel_id]


def test_voucher_channel_listing_update_duplicates_in_add_and_remove(
    staff_api_client,
    voucher,
    permission_manage_discounts,
    channel_USD,
):
    # given
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": voucher_id,
        "input": {
            "addChannels": [{"channelId": channel_id, "discountValue": 50.5}],
            "removeChannels": [channel_id],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["voucherChannelListingUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "input"
    assert errors[0]["code"] == DiscountErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["channels"] == [channel_id]


def test_voucher_channel_listing_update_invalid_precision_discount_value(
    staff_api_client,
    voucher,
    permission_manage_discounts,
    channel_USD,
):
    # given
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": voucher_id,
        "input": {
            "addChannels": [
                {
                    "channelId": channel_id,
                    "discountValue": 5.55555,
                    "minAmountSpent": 100.2,
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["voucherChannelListingUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "discountValue"
    assert errors[0]["code"] == DiscountErrorCode.INVALID.name
    assert errors[0]["channels"] == [channel_id]


def test_voucher_channel_listing_update_invalid_precision_min_amount_spent(
    staff_api_client,
    voucher,
    permission_manage_discounts,
    channel_USD,
):
    # given
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.pk)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "id": voucher_id,
        "input": {
            "addChannels": [
                {
                    "channelId": channel_id,
                    "discountValue": 5.55,
                    "minAmountSpent": 100.2222,
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CHANNEL_LISTING_UPDATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["voucherChannelListingUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "minAmountSpent"
    assert errors[0]["code"] == DiscountErrorCode.INVALID.name
    assert errors[0]["channels"] == [channel_id]


VOUCHER_CHANNEL_LISTING_UPDATE_BY_EXTERNAL_REFERENCE_MUTATION = """
mutation UpdateVoucherChannelListing(
    $id: ID, $externalReference: String, $input: VoucherChannelListingInput!
) {
    voucherChannelListingUpdate(
        id: $id, externalReference: $externalReference, input: $input
    ) {
        errors {
            field
            message
            code
        }
        voucher {
            id
            channelListings {
                channel {
                    slug
                }
                discountValue
            }
        }
    }
}
"""


def test_by_external_reference(
    staff_api_client, voucher, permission_manage_discounts, channel_USD, mocker
):
    # given
    external_reference = "voucher-ext-ref"
    voucher.external_reference = external_reference
    voucher.save(update_fields=["external_reference"])
    listing = voucher.channel_listings.get(channel=channel_USD)
    discount_value = 5
    assert listing.discount_value != discount_value
    voucher_updated = mocker.patch(
        "saleor.plugins.manager.PluginsManager.voucher_updated"
    )
    variables = {
        "externalReference": external_reference,
        "input": {
            "addChannels": [
                {
                    "channelId": graphene.Node.to_global_id("Channel", channel_USD.pk),
                    "discountValue": discount_value,
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CHANNEL_LISTING_UPDATE_BY_EXTERNAL_REFERENCE_MUTATION,
        variables=variables,
        permissions=(permission_manage_discounts,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["voucherChannelListingUpdate"]
    assert data["errors"] == []
    assert data["voucher"] == {
        "id": graphene.Node.to_global_id("Voucher", voucher.pk),
        "channelListings": [
            {"channel": {"slug": channel_USD.slug}, "discountValue": discount_value}
        ],
    }
    listing.refresh_from_db(fields=("discount_value",))
    assert listing.discount_value == discount_value
    voucher_updated.assert_called_once()


@pytest.mark.parametrize(
    ("_case", "identifiers", "error_field", "error_code", "message"),
    [
        (
            "omitted",
            {},
            None,
            DiscountErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'externalReference'.",
        ),
        (
            "null",
            {"id": None, "externalReference": None},
            None,
            DiscountErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'externalReference'.",
        ),
        (
            "empty",
            {"externalReference": ""},
            None,
            DiscountErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'externalReference'.",
        ),
        (
            "both",
            {"externalReference": "existing-reference"},
            None,
            DiscountErrorCode.GRAPHQL_ERROR,
            "Argument 'id' cannot be combined with 'externalReference'",
        ),
        (
            "not_found",
            {"externalReference": "missing-reference"},
            "externalReference",
            DiscountErrorCode.NOT_FOUND,
            "Couldn't resolve to a node: missing-reference",
        ),
    ],
)
def test_external_reference_invalid_identifiers(
    _case,
    identifiers,
    error_field,
    error_code,
    message,
    staff_api_client,
    voucher,
    permission_manage_discounts,
    channel_USD,
    mocker,
):
    # given
    voucher.external_reference = "existing-reference"
    voucher.save(update_fields=["external_reference"])
    listing = voucher.channel_listings.get(channel=channel_USD)
    original_discount_value = listing.discount_value
    voucher_updated = mocker.patch(
        "saleor.plugins.manager.PluginsManager.voucher_updated"
    )
    variables = dict(identifiers)
    if _case == "both":
        variables["id"] = graphene.Node.to_global_id("Voucher", voucher.pk)
    variables["input"] = {
        "addChannels": [
            {
                "channelId": graphene.Node.to_global_id("Channel", channel_USD.pk),
                "discountValue": 5,
            }
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CHANNEL_LISTING_UPDATE_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=(permission_manage_discounts,),
        check_no_permissions=False,
    )

    # then
    data = get_graphql_content(response)["data"]["voucherChannelListingUpdate"]
    assert data["voucher"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0] == {
        "field": error_field,
        "code": error_code.name,
        "message": message,
    }
    listing.refresh_from_db(fields=("discount_value",))
    assert listing.discount_value == original_discount_value
    voucher_updated.assert_not_called()


@pytest.mark.parametrize(
    ("_case", "client_fixture", "is_allowed"),
    [
        ("anonymous", "api_client", False),
        ("customer", "user_api_client", False),
        ("staff_without_permission", "staff_api_client", False),
        ("staff_with_permission", "staff_api_client", True),
        ("app_without_permission", "app_api_client", False),
        ("app_with_permission", "app_api_client", True),
    ],
)
def test_external_reference_authorization(
    _case,
    client_fixture,
    is_allowed,
    request,
    voucher,
    permission_manage_discounts,
    channel_USD,
    mocker,
):
    # given
    client = request.getfixturevalue(client_fixture)
    external_reference = "existing-reference"
    voucher.external_reference = external_reference
    voucher.save(update_fields=["external_reference"])
    listing = voucher.channel_listings.get(channel=channel_USD)
    original_discount_value = listing.discount_value
    discount_value = 5
    assert original_discount_value != discount_value
    voucher_updated = mocker.patch(
        "saleor.plugins.manager.PluginsManager.voucher_updated"
    )
    variables = {
        "externalReference": external_reference,
        "input": {
            "addChannels": [
                {
                    "channelId": graphene.Node.to_global_id("Channel", channel_USD.pk),
                    "discountValue": discount_value,
                }
            ]
        },
    }

    # when
    response = client.post_graphql(
        VOUCHER_CHANNEL_LISTING_UPDATE_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_discounts] if is_allowed else [],
        check_no_permissions=False,
    )

    # then
    listing.refresh_from_db(fields=("discount_value",))
    if is_allowed:
        data = get_graphql_content(response)["data"]["voucherChannelListingUpdate"]
        assert data["errors"] == []
        assert data["voucher"]["id"] == graphene.Node.to_global_id(
            "Voucher", voucher.pk
        )
        assert listing.discount_value == discount_value
        voucher_updated.assert_called_once()
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"] == {"voucherChannelListingUpdate": None}
        assert len(content["errors"]) == 1
        assert content["errors"][0]["path"] == ["voucherChannelListingUpdate"]
        assert content["errors"][0]["message"] == (
            "To access this path, you need one of the following permissions: "
            "MANAGE_DISCOUNTS"
        )
        assert listing.discount_value == original_discount_value
        voucher_updated.assert_not_called()

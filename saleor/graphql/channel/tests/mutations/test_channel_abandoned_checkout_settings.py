import datetime

import graphene
import pytest
from django.conf import settings
from django.utils import timezone
from freezegun import freeze_time

from .....channel.error_codes import ChannelErrorCode
from ....tests.utils import get_graphql_content

CHANNEL_UPDATE_MUTATION = """
    mutation UpdateChannel($id: ID!, $input: ChannelUpdateInput!) {
        channelUpdate(id: $id, input: $input) {
            channel {
                checkoutSettings {
                    abandonedCheckoutEnabled
                    abandonedCheckoutThreshold
                    abandonedCheckoutCutOffDate
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

CHANNEL_CREATE_MUTATION = """
    mutation CreateChannel($input: ChannelCreateInput!) {
        channelCreate(input: $input) {
            channel {
                checkoutSettings {
                    abandonedCheckoutEnabled
                    abandonedCheckoutThreshold
                    abandonedCheckoutCutOffDate
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


def update_abandoned_checkout(api_client, permission, channel, abandoned_checkout):
    response = api_client.post_graphql(
        CHANNEL_UPDATE_MUTATION,
        variables={
            "id": graphene.Node.to_global_id("Channel", channel.id),
            "input": {"checkoutSettings": {"abandonedCheckout": abandoned_checkout}},
        },
        permissions=(permission,),
    )
    return get_graphql_content(response)["data"]["channelUpdate"]


@freeze_time("2026-11-17 12:00:00")
def test_enable_with_defaults(
    staff_api_client, permission_manage_channels, channel_USD
):
    # given
    assert channel_USD.abandoned_checkout_enabled is False

    # when
    data = update_abandoned_checkout(
        staff_api_client, permission_manage_channels, channel_USD, {"enabled": True}
    )

    # then
    assert data["errors"] == []
    channel_USD.refresh_from_db()
    assert channel_USD.abandoned_checkout_enabled is True
    assert (
        channel_USD.abandoned_checkout_threshold
        == settings.DEFAULT_ABANDONED_CHECKOUT_THRESHOLD
    )
    assert channel_USD.abandoned_checkout_cut_off_date == timezone.now()
    assert data["channel"]["checkoutSettings"] == {
        "abandonedCheckoutEnabled": True,
        "abandonedCheckoutThreshold": settings.DEFAULT_ABANDONED_CHECKOUT_THRESHOLD,
        "abandonedCheckoutCutOffDate": timezone.now().isoformat(),
    }


def test_enable_with_threshold_and_cut_off_date(
    staff_api_client, permission_manage_channels, channel_USD
):
    # given
    threshold = 120
    cut_off_date = timezone.now() - datetime.timedelta(days=3)

    # when
    data = update_abandoned_checkout(
        staff_api_client,
        permission_manage_channels,
        channel_USD,
        {
            "enabled": True,
            "threshold": threshold,
            "cutOffDate": cut_off_date.isoformat(),
        },
    )

    # then
    assert data["errors"] == []
    channel_USD.refresh_from_db()
    assert channel_USD.abandoned_checkout_enabled is True
    assert channel_USD.abandoned_checkout_threshold == threshold
    assert channel_USD.abandoned_checkout_cut_off_date == cut_off_date


def test_enable_again_keeps_threshold_and_cut_off_date(
    staff_api_client, permission_manage_channels, channel_USD
):
    # given
    threshold = 120
    cut_off_date = timezone.now() - datetime.timedelta(days=3)
    channel_USD.abandoned_checkout_enabled = True
    channel_USD.abandoned_checkout_threshold = threshold
    channel_USD.abandoned_checkout_cut_off_date = cut_off_date
    channel_USD.save()

    # when
    data = update_abandoned_checkout(
        staff_api_client, permission_manage_channels, channel_USD, {"enabled": True}
    )

    # then
    assert data["errors"] == []
    channel_USD.refresh_from_db()
    assert channel_USD.abandoned_checkout_threshold == threshold
    assert channel_USD.abandoned_checkout_cut_off_date == cut_off_date


def test_disable_clears_threshold_and_cut_off_date(
    staff_api_client, permission_manage_channels, channel_USD
):
    # given
    channel_USD.abandoned_checkout_enabled = True
    channel_USD.abandoned_checkout_threshold = 120
    channel_USD.abandoned_checkout_cut_off_date = timezone.now()
    channel_USD.save()

    # when
    data = update_abandoned_checkout(
        staff_api_client, permission_manage_channels, channel_USD, {"enabled": False}
    )

    # then
    assert data["errors"] == []
    channel_USD.refresh_from_db()
    assert channel_USD.abandoned_checkout_enabled is False
    assert channel_USD.abandoned_checkout_threshold is None
    assert channel_USD.abandoned_checkout_cut_off_date is None


@pytest.mark.parametrize(
    ("field", "label", "value"),
    [
        ("threshold", "threshold", 60),
        ("cutOffDate", "cut-off date", "2026-11-17T12:00:00+00:00"),
    ],
)
def test_disable_with_value_set(
    field, label, value, staff_api_client, permission_manage_channels, channel_USD
):
    # when
    data = update_abandoned_checkout(
        staff_api_client,
        permission_manage_channels,
        channel_USD,
        {"enabled": False, field: value},
    )

    # then
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == field
    assert error["code"] == ChannelErrorCode.INVALID.name
    assert error["message"] == (
        f"The {label} cannot be set when abandoned checkout event is disabled."
    )
    channel_USD.refresh_from_db()
    assert channel_USD.abandoned_checkout_enabled is False


def test_enable_with_zero_threshold(
    staff_api_client, permission_manage_channels, channel_USD
):
    # when
    data = update_abandoned_checkout(
        staff_api_client,
        permission_manage_channels,
        channel_USD,
        {"enabled": True, "threshold": 0},
    )

    # then
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "threshold"
    assert error["code"] == ChannelErrorCode.INVALID.name
    assert error["message"] == "The threshold must be at least 1 minute."
    channel_USD.refresh_from_db()
    assert channel_USD.abandoned_checkout_enabled is False


@freeze_time("2026-11-17 12:00:00")
def test_channel_create_with_abandoned_checkout(
    staff_api_client, permission_manage_channels
):
    # given
    threshold = 45
    variables = {
        "input": {
            "name": "Channel",
            "slug": "channel-abandoned",
            "currencyCode": "USD",
            "defaultCountry": "US",
            "checkoutSettings": {
                "abandonedCheckout": {"enabled": True, "threshold": threshold}
            },
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )

    # then
    data = get_graphql_content(response)["data"]["channelCreate"]
    assert data["errors"] == []
    assert data["channel"]["checkoutSettings"] == {
        "abandonedCheckoutEnabled": True,
        "abandonedCheckoutThreshold": threshold,
        "abandonedCheckoutCutOffDate": timezone.now().isoformat(),
    }

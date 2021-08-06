from unittest import mock

import graphene

from .....giftcard import GiftCardEvents
from .....giftcard.error_codes import GiftCardErrorCode
from .....giftcard.models import GiftCardEvent
from ....tests.utils import assert_no_permission, get_graphql_content

GIFT_CARD_RESEND_MUTATION = """
    mutation giftCardResend($input: GiftCardResendInput!) {
        giftCardResend(input: $input) {
            giftCard {
                id
                code
                createdBy {
                    email
                }
                usedBy {
                    email
                }
                createdByEmail
                usedByEmail
                app {
                    name
                }
                events {
                    type
                    user {
                        email
                    }
                    app {
                        name
                    }
                }
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_resend_gift_card(
    notify_mock,
    staff_api_client,
    gift_card,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    email = "gift_card_receiver@example.com"
    variables = {
        "input": {
            "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
            "email": email,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        GIFT_CARD_RESEND_MUTATION,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_users,
            permission_manage_apps,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardResend"]["giftCard"]
    errors = content["data"]["giftCardResend"]["errors"]

    assert not errors
    events = data["events"]
    assert len(events) == 1
    event = events[0]
    assert event["type"] == GiftCardEvents.RESENT.upper()
    assert event["user"]["email"] == staff_api_client.user.email

    db_event = GiftCardEvent.objects.get()
    assert db_event.parameters["email"] == email

    assert notify_mock.call_count == 1


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_resend_gift_card_as_app(
    notify_mock,
    app_api_client,
    gift_card,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    variables = {
        "input": {
            "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        }
    }

    # when
    response = app_api_client.post_graphql(
        GIFT_CARD_RESEND_MUTATION,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_users,
            permission_manage_apps,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardResend"]["giftCard"]
    errors = content["data"]["giftCardResend"]["errors"]

    assert not errors
    events = data["events"]
    assert len(events) == 1
    event = events[0]
    assert event["type"] == GiftCardEvents.RESENT.upper()
    assert event["user"] is None
    assert event["app"]["name"] == app_api_client.app.name

    db_event = GiftCardEvent.objects.get()
    assert db_event.parameters["email"] == gift_card.created_by_email

    assert notify_mock.call_count == 1


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_update_gift_card_no_permission(
    notify_mock,
    staff_api_client,
    gift_card,
):
    # given
    variables = {
        "input": {
            "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        }
    }

    # when
    response = staff_api_client.post_graphql(
        GIFT_CARD_RESEND_MUTATION,
        variables,
    )

    # then
    assert not GiftCardEvent.objects.exists()
    assert_no_permission(response)

    notify_mock.assert_not_called()


@mock.patch("saleor.plugins.manager.PluginsManager.notify")
def test_resend_gift_card_malformed_email(
    notify_mock,
    staff_api_client,
    gift_card,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    variables = {
        "input": {
            "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
            "email": "malformed",
        }
    }

    # when
    response = staff_api_client.post_graphql(
        GIFT_CARD_RESEND_MUTATION,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_users,
            permission_manage_apps,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardResend"]["giftCard"]
    errors = content["data"]["giftCardResend"]["errors"]

    assert not data
    assert not GiftCardEvent.objects.exists()
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "email"
    assert error["code"] == GiftCardErrorCode.INVALID.name

    notify_mock.assert_not_called()

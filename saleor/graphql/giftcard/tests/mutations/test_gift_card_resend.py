from datetime import date, timedelta
from unittest import mock

import graphene

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


@mock.patch("saleor.graphql.giftcard.mutations.send_gift_card_notification")
def test_resend_gift_card(
    send_notification_mock,
    staff_api_client,
    gift_card,
    channel_USD,
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
            "channel": channel_USD.slug,
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
    assert data

    send_notification_mock.assert_called_once_with(
        staff_api_client.user,
        None,
        None,
        email,
        gift_card,
        mock.ANY,
        channel_slug=channel_USD.slug,
        resending=True,
    )


@mock.patch("saleor.graphql.giftcard.mutations.send_gift_card_notification")
def test_resend_gift_card_as_app(
    send_notification_mock,
    app_api_client,
    gift_card,
    channel_USD,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    variables = {
        "input": {
            "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
            "channel": channel_USD.slug,
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

    assert data
    assert not errors
    send_notification_mock.assert_called_once_with(
        None,
        app_api_client.app,
        gift_card.created_by,
        gift_card.created_by_email,
        gift_card,
        mock.ANY,
        channel_slug=channel_USD.slug,
        resending=True,
    )


@mock.patch("saleor.graphql.giftcard.mutations.send_gift_card_notification")
def test_update_gift_card_no_permission(
    send_notification_mock,
    staff_api_client,
    gift_card,
    channel_USD,
):
    # given
    variables = {
        "input": {
            "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
            "channel": channel_USD.slug,
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

    send_notification_mock.assert_not_called()


@mock.patch("saleor.graphql.giftcard.mutations.send_gift_card_notification")
def test_resend_gift_card_malformed_email(
    send_notification_mock,
    staff_api_client,
    gift_card,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
    channel_USD,
):
    # given
    variables = {
        "input": {
            "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
            "email": "malformed",
            "channel": channel_USD.slug,
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

    send_notification_mock.assert_not_called()


def test_resend_gift_card_expired_card(
    staff_api_client,
    gift_card,
    channel_USD,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    gift_card.expiry_date = date.today() - timedelta(days=1)
    gift_card.save(update_fields=["expiry_date"])

    email = "gift_card_receiver@example.com"
    variables = {
        "input": {
            "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
            "email": email,
            "channel": channel_USD.slug,
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
    data = content["data"]["giftCardResend"]
    errors = data["errors"]

    assert not data["giftCard"]
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "id"
    assert error["code"] == GiftCardErrorCode.EXPIRED_GIFT_CARD.name

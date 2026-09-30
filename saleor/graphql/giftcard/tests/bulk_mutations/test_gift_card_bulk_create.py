import datetime
from unittest import mock

import graphene
import pytest
from prices import Money

from .....giftcard import GiftCardEvents
from .....giftcard.error_codes import GiftCardErrorCode
from .....giftcard.models import GiftCard, GiftCardTag
from ....tests.utils import assert_no_permission, get_graphql_content

GIFT_CARD_BULK_CREATE_MUTATION = """
    mutation GiftCardBulkCreate($input: GiftCardBulkCreateInput!) {
        giftCardBulkCreate(input: $input) {
            count
            giftCards {
                id
                code
                last4CodeChars
                isActive
                expiryDate
                tags {
                    name
                }
                created
                lastUsedOn
                initialBalance {
                    currency
                    amount
                }
                currentBalance {
                    currency
                    amount
                }
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
                product {
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
                    balance {
                        initialBalance {
                            amount
                            currency
                        }
                        oldInitialBalance {
                            amount
                            currency
                        }
                        currentBalance {
                            amount
                            currency
                        }
                        oldCurrentBalance {
                            amount
                            currency
                        }
                    }
                }
            }
            errors {
                code
                field
                message
            }
        }
    }
"""


def test_create_never_expiry_gift_cards(
    staff_api_client,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    initial_balance = 100
    currency = "USD"
    tags = ["gift-card-tag", "gift-card-tag-2"]
    count = 10
    is_active = True
    variables = {
        "input": {
            "count": count,
            "balance": {
                "amount": initial_balance,
                "currency": currency,
            },
            "tags": tags,
            "isActive": is_active,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        GIFT_CARD_BULK_CREATE_MUTATION,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_users,
            permission_manage_apps,
        ],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["giftCardBulkCreate"]["errors"]
    data = content["data"]["giftCardBulkCreate"]

    assert not errors
    assert data["count"] == count
    assert len(data["giftCards"]) == count
    for card_data in data["giftCards"]:
        assert card_data["isActive"] == is_active
        assert len(card_data["tags"]) == len(tags)
        assert {tag["name"] for tag in card_data["tags"]} == set(tags)
        assert card_data["expiryDate"] is None
        assert card_data["usedBy"] is None
        assert card_data["usedByEmail"] is None
        assert card_data["createdBy"]["email"] == staff_api_client.user.email
        assert card_data["createdByEmail"] == staff_api_client.user.email
        assert card_data["app"] is None
        assert card_data["product"] is None
        assert card_data["initialBalance"]["amount"] == initial_balance
        assert card_data["initialBalance"]["currency"] == currency
        assert card_data["currentBalance"]["amount"] == initial_balance
        assert card_data["currentBalance"]["currency"] == currency
        assert len(card_data["events"]) == 1
        assert card_data["events"][0]["type"] == GiftCardEvents.ISSUED.upper()
        assert card_data["events"][0]["app"] is None
        assert card_data["events"][0]["user"]["email"] == staff_api_client.user.email
        assert (
            card_data["events"][0]["balance"]["initialBalance"]["amount"]
            == initial_balance
        )
        assert (
            card_data["events"][0]["balance"]["initialBalance"]["currency"] == currency
        )
        assert (
            card_data["events"][0]["balance"]["currentBalance"]["amount"]
            == initial_balance
        )
        assert (
            card_data["events"][0]["balance"]["currentBalance"]["currency"] == currency
        )
        assert not card_data["events"][0]["balance"]["oldInitialBalance"]
        assert not card_data["events"][0]["balance"]["oldCurrentBalance"]


@mock.patch(
    "saleor.graphql.giftcard.bulk_mutations."
    "gift_card_bulk_create.get_webhooks_for_event"
)
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_create_gift_cards_trigger_webhooks(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    initial_balance = 100
    currency = "USD"
    tags = ["gift-card-tag", "gift-card-tag-2"]
    count = 10
    is_active = True
    variables = {
        "input": {
            "count": count,
            "balance": {
                "amount": initial_balance,
                "currency": currency,
            },
            "tags": tags,
            "isActive": is_active,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        GIFT_CARD_BULK_CREATE_MUTATION,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_users,
            permission_manage_apps,
        ],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["giftCardBulkCreate"]["errors"]
    data = content["data"]["giftCardBulkCreate"]

    assert not errors
    assert data["count"] == count
    assert len(data["giftCards"]) == count
    assert mocked_webhook_trigger.call_count == count


def test_create_gift_cards_with_expiry_date_by_app(
    app_api_client,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    initial_balance = 100
    currency = "USD"
    tag = "gift-card-tag"
    count = 5
    is_active = False
    date_value = datetime.datetime.now(tz=datetime.UTC).date() + datetime.timedelta(
        days=365
    )
    variables = {
        "input": {
            "count": count,
            "balance": {
                "amount": initial_balance,
                "currency": currency,
            },
            "tags": [tag],
            "isActive": is_active,
            "expiryDate": date_value,
        }
    }

    # when
    response = app_api_client.post_graphql(
        GIFT_CARD_BULK_CREATE_MUTATION,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_users,
            permission_manage_apps,
        ],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["giftCardBulkCreate"]["errors"]
    data = content["data"]["giftCardBulkCreate"]

    assert not errors
    assert data["count"] == count
    assert len(data["giftCards"]) == count
    for card_data in data["giftCards"]:
        assert card_data["isActive"] == is_active
        assert len(card_data["tags"]) == 1
        assert card_data["tags"][0]["name"] == tag
        assert card_data["expiryDate"] == date_value.isoformat()
        assert card_data["usedBy"] is None
        assert card_data["usedByEmail"] is None
        assert card_data["createdBy"] is None
        assert card_data["createdByEmail"] is None
        assert card_data["app"]["name"] == app_api_client.app.name
        assert card_data["product"] is None
        assert card_data["initialBalance"]["amount"] == initial_balance
        assert card_data["initialBalance"]["currency"] == currency
        assert card_data["currentBalance"]["amount"] == initial_balance
        assert card_data["currentBalance"]["currency"] == currency
        assert len(card_data["events"]) == 1
        assert card_data["events"][0]["type"] == GiftCardEvents.ISSUED.upper()
        assert card_data["events"][0]["app"]["name"] == app_api_client.app.name
        assert card_data["events"][0]["user"] is None
        assert (
            card_data["events"][0]["balance"]["initialBalance"]["amount"]
            == initial_balance
        )
        assert (
            card_data["events"][0]["balance"]["initialBalance"]["currency"] == currency
        )
        assert (
            card_data["events"][0]["balance"]["currentBalance"]["amount"]
            == initial_balance
        )
        assert (
            card_data["events"][0]["balance"]["currentBalance"]["currency"] == currency
        )
        assert not card_data["events"][0]["balance"]["oldInitialBalance"]
        assert not card_data["events"][0]["balance"]["oldCurrentBalance"]


GIFT_CARD_BULK_CREATE_TAGS_MUTATION = """
    mutation GiftCardBulkCreate($input: GiftCardBulkCreateInput!) {
        giftCardBulkCreate(input: $input) {
            count
            giftCards {
                id
                tags {
                    name
                }
            }
            errors {
                code
                field
                message
            }
        }
    }
"""


def test_create_gift_cards_normalizes_tag_names(
    staff_api_client,
    gift_card,
    permission_manage_gift_card,
):
    # given
    existing_tag = gift_card.tags.first().name
    new_tag = "new-tag"
    tags_count = GiftCardTag.objects.count()
    count = 3
    variables = {
        "input": {
            "count": count,
            "balance": {
                "amount": 100,
                "currency": "USD",
            },
            "tags": [existing_tag.upper(), existing_tag, new_tag.upper(), new_tag],
            "isActive": True,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        GIFT_CARD_BULK_CREATE_TAGS_MUTATION,
        variables,
        permissions=[permission_manage_gift_card],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["giftCardBulkCreate"]["errors"]
    data = content["data"]["giftCardBulkCreate"]

    assert not errors
    assert data["count"] == count
    for card_data in data["giftCards"]:
        assert {tag["name"] for tag in card_data["tags"]} == {existing_tag, new_tag}
    # only one lower-cased tag is created, the existing one is reused
    assert GiftCardTag.objects.count() == tags_count + 1


@pytest.mark.parametrize(
    ("first_batch_tags", "second_batch_tags"),
    [
        (["tag-1"], ["tag-1"]),
        (["tag-1", "tag-2"], ["tag-1", "tag-2"]),
        (["tag-1", "tag-2", "tag-3"], ["tag-2", "tag-3", "tag-4"]),
        (["tag-1", "tag-2"], ["tag-3"]),
    ],
)
def test_create_gift_cards_with_tags_keeps_tags_of_previously_created_gift_cards_intact(
    first_batch_tags,
    second_batch_tags,
    staff_api_client,
    permission_manage_gift_card,
):
    # given
    first_batch = GiftCard.objects.bulk_create(
        [
            GiftCard(
                code=f"first-batch-{index}",
                initial_balance=Money(10, "USD"),
                current_balance=Money(10, "USD"),
            )
            for index in range(10)
        ]
    )
    first_batch_ids = {gift_card.id for gift_card in first_batch}
    first_batch_tag_instances = GiftCardTag.objects.bulk_create(
        [GiftCardTag(name=tag) for tag in first_batch_tags]
    )
    for gift_card in first_batch:
        gift_card.tags.add(*first_batch_tag_instances)
    second_count = 3
    variables = {
        "input": {
            "count": second_count,
            "balance": {
                "amount": 100,
                "currency": "USD",
            },
            "tags": second_batch_tags,
            "isActive": True,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        GIFT_CARD_BULK_CREATE_TAGS_MUTATION,
        variables,
        permissions=[permission_manage_gift_card],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["giftCardBulkCreate"]["errors"]
    data = content["data"]["giftCardBulkCreate"]

    assert not errors
    assert data["count"] == second_count
    second_batch_ids = {
        int(graphene.Node.from_global_id(card_data["id"])[1])
        for card_data in data["giftCards"]
    }
    for card_data in data["giftCards"]:
        assert {tag["name"] for tag in card_data["tags"]} == set(second_batch_tags)
    all_tags = set(first_batch_tags) | set(second_batch_tags)
    for tag in all_tags:
        expected_ids = set()
        if tag in first_batch_tags:
            expected_ids.update(first_batch_ids)
        if tag in second_batch_tags:
            expected_ids.update(second_batch_ids)
        tagged_ids = set(
            GiftCardTag.objects.get(name=tag).gift_cards.values_list("id", flat=True)
        )
        assert tagged_ids == expected_ids, (
            f"gift cards assigned to tag {tag} do not match"
        )


def test_create_gift_cards_by_cutomer(api_client):
    # given
    initial_balance = 100
    currency = "USD"
    tag = "gift-card-tag"
    count = 10
    is_active = True
    variables = {
        "input": {
            "count": count,
            "balance": {
                "amount": initial_balance,
                "currency": currency,
            },
            "tags": [tag],
            "isActive": is_active,
        }
    }

    # when
    response = api_client.post_graphql(
        GIFT_CARD_BULK_CREATE_MUTATION,
        variables,
    )

    # then
    assert_no_permission(response)


@pytest.mark.parametrize("count_value", [0, -2])
def test_create_gift_cards_invalid_count_value(
    count_value,
    app_api_client,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    initial_balance = 100
    currency = "USD"
    tag = "gift-card-tag"
    is_active = False
    date_value = datetime.datetime.now(tz=datetime.UTC).date() + datetime.timedelta(
        days=365
    )
    variables = {
        "input": {
            "count": count_value,
            "balance": {
                "amount": initial_balance,
                "currency": currency,
            },
            "tags": [tag],
            "isActive": is_active,
            "expiryDate": date_value,
        }
    }

    # when
    response = app_api_client.post_graphql(
        GIFT_CARD_BULK_CREATE_MUTATION,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_users,
            permission_manage_apps,
        ],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["giftCardBulkCreate"]["errors"]
    data = content["data"]["giftCardBulkCreate"]

    assert not data["giftCards"]
    assert data["count"] == 0
    assert len(errors) == 1
    assert errors[0]["field"] == "count"
    assert errors[0]["code"] == GiftCardErrorCode.INVALID.name


def test_create_gift_cards_too_many_decimal_places_in_balance_amount(
    app_api_client,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    initial_balance = 14.3455
    currency = "USD"
    tag = "gift-card-tag"
    is_active = False
    date_value = datetime.datetime.now(tz=datetime.UTC).date() + datetime.timedelta(
        days=365
    )
    variables = {
        "input": {
            "count": 2,
            "balance": {
                "amount": initial_balance,
                "currency": currency,
            },
            "tags": [tag],
            "isActive": is_active,
            "expiryDate": date_value,
        }
    }

    # when
    response = app_api_client.post_graphql(
        GIFT_CARD_BULK_CREATE_MUTATION,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_users,
            permission_manage_apps,
        ],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["giftCardBulkCreate"]["errors"]
    data = content["data"]["giftCardBulkCreate"]

    assert not data["giftCards"]
    assert data["count"] == 0
    assert len(errors) == 1
    assert errors[0]["field"] == "balance"
    assert errors[0]["code"] == GiftCardErrorCode.INVALID.name


def test_create_gift_cards_zero_balance_amount(
    app_api_client,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    initial_balance = 0
    currency = "USD"
    tag = "gift-card-tag"
    is_active = False
    date_value = datetime.datetime.now(tz=datetime.UTC).date() + datetime.timedelta(
        days=365
    )
    variables = {
        "input": {
            "count": 2,
            "balance": {
                "amount": initial_balance,
                "currency": currency,
            },
            "tags": [tag],
            "isActive": is_active,
            "expiryDate": date_value,
        }
    }

    # when
    response = app_api_client.post_graphql(
        GIFT_CARD_BULK_CREATE_MUTATION,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_users,
            permission_manage_apps,
        ],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["giftCardBulkCreate"]["errors"]
    data = content["data"]["giftCardBulkCreate"]

    assert not data["giftCards"]
    assert data["count"] == 0
    assert len(errors) == 1
    assert errors[0]["field"] == "balance"
    assert errors[0]["code"] == GiftCardErrorCode.INVALID.name


@pytest.mark.parametrize(
    "date_value",
    [datetime.date(1999, 1, 1), datetime.datetime.now(tz=datetime.UTC).date()],
)
def test_create_gift_cards_invalid_expiry_date(
    date_value,
    app_api_client,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    initial_balance = 10
    currency = "USD"
    tag = "gift-card-tag"
    is_active = False
    variables = {
        "input": {
            "count": 2,
            "balance": {
                "amount": initial_balance,
                "currency": currency,
            },
            "tags": [tag],
            "isActive": is_active,
            "expiryDate": date_value,
        }
    }

    # when
    response = app_api_client.post_graphql(
        GIFT_CARD_BULK_CREATE_MUTATION,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_users,
            permission_manage_apps,
        ],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["giftCardBulkCreate"]["errors"]
    data = content["data"]["giftCardBulkCreate"]

    assert not data["giftCards"]
    assert data["count"] == 0
    assert len(errors) == 1
    assert errors[0]["field"] == "expiryDate"
    assert errors[0]["code"] == GiftCardErrorCode.INVALID.name

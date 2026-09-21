import datetime
from unittest.mock import patch

import graphene
import pytest
from django.utils import timezone
from freezegun import freeze_time

from .....discount import PromotionEvents
from .....discount.error_codes import PromotionCreateErrorCode, PromotionUpdateErrorCode
from .....discount.models import PromotionEvent
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

PROMOTION_UPDATE_MUTATION = """
    mutation promotionUpdate($id: ID!, $input: PromotionUpdateInput!) {
        promotionUpdate(id: $id, input: $input) {
            promotion {
                id
                name
                description
                startDate
                endDate
                createdAt
                updatedAt
                events {
                    ... on PromotionEventInterface {
                        type
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


MUTATION_UPDATE_PROMOTION_BY_EXTERNAL_REFERENCE = """
    mutation updatePromotion(
        $id: ID, $externalReference: String, $input: PromotionUpdateInput!
    ) {
        promotionUpdate(
            id: $id, externalReference: $externalReference, input: $input
        ) {
            errors {
                message
                field
                code
            }
            promotion {
                name
                externalReference
            }
        }
    }
"""


def test_update_promotion_by_external_reference(
    staff_api_client, catalogue_promotion, permission_manage_discounts
):
    # given
    external_reference = "test-ext-ref"
    catalogue_promotion.external_reference = external_reference
    catalogue_promotion.save(update_fields=["external_reference"])
    name = "New name"
    variables = {
        "externalReference": external_reference,
        "input": {"name": name},
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_PROMOTION_BY_EXTERNAL_REFERENCE,
        variables=variables,
        permissions=[permission_manage_discounts],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["promotionUpdate"]
    assert data["errors"] == []
    catalogue_promotion.refresh_from_db(fields=("name", "external_reference"))
    assert data["promotion"]["name"] == name
    assert catalogue_promotion.name == name
    assert catalogue_promotion.external_reference == external_reference


def test_update_promotion_with_non_unique_external_reference(
    staff_api_client, catalogue_promotion, promotion_list, permission_manage_discounts
):
    # given
    external_reference = "test-ext-ref"
    other_promotion = promotion_list[0]
    other_promotion.external_reference = external_reference
    other_promotion.save(update_fields=["external_reference"])

    variables = {
        "id": graphene.Node.to_global_id("Promotion", catalogue_promotion.pk),
        "input": {"externalReference": external_reference},
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_PROMOTION_BY_EXTERNAL_REFERENCE,
        variables=variables,
        permissions=[permission_manage_discounts],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["promotionUpdate"]
    catalogue_promotion.refresh_from_db(fields=("external_reference",))
    assert catalogue_promotion.external_reference is None
    assert data["promotion"] is None
    errors = data["errors"]
    assert len(errors) == 1
    assert (
        errors[0]["message"] == "Promotion with this External reference already exists."
    )
    assert errors[0]["field"] == "externalReference"
    assert errors[0]["code"] == PromotionUpdateErrorCode.UNIQUE.name


@pytest.mark.parametrize(
    ("_case", "identifiers", "error_field", "error_code", "message"),
    [
        (
            "omitted",
            {},
            None,
            PromotionUpdateErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'external_reference'.",
        ),
        (
            "null",
            {"id": None, "externalReference": None},
            None,
            PromotionUpdateErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'external_reference'.",
        ),
        (
            "empty",
            {"externalReference": ""},
            None,
            PromotionUpdateErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'external_reference'.",
        ),
        (
            "both",
            {"externalReference": "existing-reference"},
            None,
            PromotionUpdateErrorCode.GRAPHQL_ERROR,
            "Argument 'id' cannot be combined with 'external_reference'",
        ),
        (
            "not_found",
            {"externalReference": "missing-reference"},
            "externalReference",
            PromotionUpdateErrorCode.NOT_FOUND,
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
    catalogue_promotion,
    permission_manage_discounts,
    mocker,
):
    # given
    catalogue_promotion.external_reference = "existing-reference"
    catalogue_promotion.save(update_fields=("external_reference",))
    original_name = catalogue_promotion.name
    original_reference = catalogue_promotion.external_reference
    webhook = mocker.patch("saleor.plugins.manager.PluginsManager.promotion_updated")
    variables = dict(identifiers)
    if _case == "both":
        variables["id"] = graphene.Node.to_global_id(
            "Promotion", catalogue_promotion.pk
        )
    variables["input"] = {"name": "Changed name"}

    # when
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_PROMOTION_BY_EXTERNAL_REFERENCE,
        variables,
        permissions=[permission_manage_discounts],
        check_no_permissions=False,
    )

    # then
    data = get_graphql_content(response)["data"]["promotionUpdate"]
    assert data["promotion"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0] == {
        "field": error_field,
        "code": error_code.name,
        "message": message,
    }
    catalogue_promotion.refresh_from_db(fields=("name", "external_reference"))
    assert catalogue_promotion.name == original_name
    assert catalogue_promotion.external_reference == original_reference
    webhook.assert_not_called()


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
    catalogue_promotion,
    permission_manage_discounts,
    mocker,
):
    # given
    client = request.getfixturevalue(client_fixture)
    catalogue_promotion.external_reference = "existing-reference"
    catalogue_promotion.save(update_fields=("external_reference",))
    original_name = catalogue_promotion.name
    original_reference = catalogue_promotion.external_reference
    name = "Changed promotion"
    webhook = mocker.patch("saleor.plugins.manager.PluginsManager.promotion_updated")
    variables = {"externalReference": original_reference, "input": {"name": name}}

    # when
    response = client.post_graphql(
        MUTATION_UPDATE_PROMOTION_BY_EXTERNAL_REFERENCE,
        variables,
        permissions=[permission_manage_discounts] if is_allowed else [],
        check_no_permissions=False,
    )

    # then
    if is_allowed:
        data = get_graphql_content(response)["data"]["promotionUpdate"]
        assert data["errors"] == []
        catalogue_promotion.refresh_from_db(fields=("name", "external_reference"))
        assert catalogue_promotion.name == name
        assert catalogue_promotion.external_reference == original_reference
        assert data["promotion"] == {
            "name": name,
            "externalReference": original_reference,
        }
        webhook.assert_called_once()
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"] == {"promotionUpdate": None}
        assert len(content["errors"]) == 1
        assert content["errors"][0]["path"] == ["promotionUpdate"]
        assert content["errors"][0]["message"] == (
            "To access this path, you need one of the following permissions: MANAGE_DISCOUNTS"
        )
        catalogue_promotion.refresh_from_db(fields=("name", "external_reference"))
        assert catalogue_promotion.name == original_name
        assert catalogue_promotion.external_reference == original_reference
        webhook.assert_not_called()


@pytest.mark.parametrize(
    ("_case", "reference_input", "expected_reference"),
    [
        ("changed", {"externalReference": "new-reference"}, "new-reference"),
        ("cleared", {"externalReference": None}, None),
        ("omitted", {}, "original-reference"),
    ],
)
def test_external_reference_input(
    _case,
    reference_input,
    expected_reference,
    staff_api_client,
    catalogue_promotion,
    permission_manage_discounts,
):
    # given
    catalogue_promotion.external_reference = "original-reference"
    catalogue_promotion.save(update_fields=("external_reference",))
    name = "Updated promotion"
    variables = {
        "externalReference": catalogue_promotion.external_reference,
        "input": {"name": name, **reference_input},
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_PROMOTION_BY_EXTERNAL_REFERENCE,
        variables,
        permissions=[permission_manage_discounts],
    )

    # then
    data = get_graphql_content(response)["data"]["promotionUpdate"]
    assert data["errors"] == []
    assert data["promotion"] == {"name": name, "externalReference": expected_reference}
    catalogue_promotion.refresh_from_db(fields=("name", "external_reference"))
    assert catalogue_promotion.name == name
    assert catalogue_promotion.external_reference == expected_reference


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.plugins.manager.PluginsManager.promotion_started")
@patch("saleor.plugins.manager.PluginsManager.promotion_updated")
def test_promotion_update_by_staff_user(
    promotion_updated_mock,
    promotion_started_mock,
    staff_api_client,
    permission_group_manage_discounts,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    start_date = timezone.now() - datetime.timedelta(days=1)
    end_date = timezone.now() + datetime.timedelta(days=10)

    new_promotion_name = "new test promotion"
    variables = {
        "id": graphene.Node.to_global_id("Promotion", promotion.id),
        "input": {
            "name": new_promotion_name,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
        },
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionUpdate"]
    promotion_data = data["promotion"]

    assert not data["errors"]
    assert promotion_data["name"] == new_promotion_name
    assert promotion_data["description"] == promotion.description
    assert promotion_data["startDate"] == start_date.isoformat()
    assert promotion_data["endDate"] == end_date.isoformat()
    assert promotion_data["createdAt"] == promotion.created_at.isoformat()
    assert promotion_data["updatedAt"] == timezone.now().isoformat()
    event_types = [event["type"] for event in promotion_data["events"]]
    assert PromotionEvents.PROMOTION_UPDATED.upper() in event_types
    assert PromotionEvents.PROMOTION_STARTED.upper() in event_types

    promotion.refresh_from_db()
    assert promotion.last_notification_scheduled_at == timezone.now()

    promotion_updated_mock.assert_called_once_with(promotion)
    promotion_started_mock.assert_called_once_with(promotion)
    for rule in promotion.rules.all():
        assert rule.variants_dirty is True


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.plugins.manager.PluginsManager.promotion_ended")
@patch("saleor.plugins.manager.PluginsManager.promotion_updated")
def test_promotion_update_by_app(
    promotion_updated_mock,
    promotion_ended_mock,
    app_api_client,
    permission_manage_discounts,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    promotion.start_date = timezone.now()
    promotion.end_date = None
    promotion.save(update_fields=["start_date", "end_date"])

    end_date = timezone.now() + datetime.timedelta(days=2)

    new_promotion_name = "new test promotion"
    variables = {
        "id": graphene.Node.to_global_id("Promotion", promotion.id),
        "input": {
            "name": new_promotion_name,
            "endDate": end_date.isoformat(),
        },
    }

    # when
    response = app_api_client.post_graphql(
        PROMOTION_UPDATE_MUTATION, variables, permissions=(permission_manage_discounts,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionUpdate"]
    promotion_data = data["promotion"]

    assert not data["errors"]
    assert promotion_data["name"] == new_promotion_name
    assert promotion_data["description"] == promotion.description
    assert promotion_data["endDate"] == end_date.isoformat()
    assert promotion_data["createdAt"] == promotion.created_at.isoformat()
    assert promotion_data["updatedAt"] == timezone.now().isoformat()
    event_types = [event["type"] for event in promotion_data["events"]]
    assert PromotionEvents.PROMOTION_UPDATED.upper() in event_types
    assert PromotionEvents.PROMOTION_ENDED.upper() not in event_types

    promotion_updated_mock.assert_called_once_with(promotion)
    promotion_ended_mock.assert_not_called()
    for rule in promotion.rules.all():
        assert rule.variants_dirty is True


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.plugins.manager.PluginsManager.promotion_started")
@patch("saleor.plugins.manager.PluginsManager.promotion_ended")
@patch("saleor.plugins.manager.PluginsManager.promotion_updated")
def test_promotion_update_dates_dont_change(
    promotion_updated_mock,
    promotion_started_mock,
    promotion_ended_mock,
    staff_api_client,
    permission_group_manage_discounts,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    promotion.last_notification_scheduled_at = timezone.now() - datetime.timedelta(
        hours=1
    )
    promotion.save(update_fields=["last_notification_scheduled_at"])

    previous_notification_date = promotion.last_notification_scheduled_at

    new_promotion_name = "new test promotion"
    variables = {
        "id": graphene.Node.to_global_id("Promotion", promotion.id),
        "input": {
            "name": new_promotion_name,
        },
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionUpdate"]
    promotion_data = data["promotion"]

    assert not data["errors"]
    assert promotion_data["name"] == new_promotion_name
    assert promotion_data["description"] == promotion.description
    assert promotion_data["startDate"] == promotion.start_date.isoformat()
    assert promotion_data["endDate"] == promotion.end_date.isoformat()
    assert promotion_data["createdAt"] == promotion.created_at.isoformat()
    assert promotion_data["updatedAt"] == timezone.now().isoformat()

    event_types = [event["type"] for event in promotion_data["events"]]
    assert PromotionEvents.PROMOTION_UPDATED.upper() in event_types
    assert PromotionEvents.PROMOTION_STARTED.upper() not in event_types
    assert PromotionEvents.PROMOTION_ENDED.upper() not in event_types

    promotion.refresh_from_db()
    assert promotion.last_notification_scheduled_at == previous_notification_date

    promotion_updated_mock.assert_called_once_with(promotion)
    promotion_started_mock.assert_not_called()
    promotion_ended_mock.assert_not_called()
    for rule in promotion.rules.all():
        assert rule.variants_dirty is False


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.plugins.manager.PluginsManager.promotion_started")
@patch("saleor.plugins.manager.PluginsManager.promotion_ended")
@patch("saleor.plugins.manager.PluginsManager.promotion_updated")
def test_promotion_update_by_customer(
    promotion_updated_mock,
    promotion_started_mock,
    promotion_ended_mock,
    api_client,
    catalogue_promotion,
):
    # given
    promotion = catalogue_promotion
    start_date = timezone.now() + datetime.timedelta(days=1)
    end_date = timezone.now() + datetime.timedelta(days=10)

    new_promotion_name = "new test promotion"
    variables = {
        "id": graphene.Node.to_global_id("Promotion", promotion.id),
        "input": {
            "name": new_promotion_name,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
        },
    }

    # when
    response = api_client.post_graphql(PROMOTION_UPDATE_MUTATION, variables)

    # then
    assert_no_permission(response)

    promotion_updated_mock.assert_not_called()
    promotion_started_mock.assert_not_called()
    promotion_ended_mock.assert_not_called()
    for rule in promotion.rules.all():
        assert rule.variants_dirty is False


@freeze_time("2020-03-18 12:00:00")
def test_promotion_update_end_date_before_start_date(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    catalogue_promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    start_date = timezone.now() + datetime.timedelta(days=1)
    end_date = timezone.now() - datetime.timedelta(days=10)

    new_promotion_name = "new test promotion"
    variables = {
        "id": graphene.Node.to_global_id("Promotion", catalogue_promotion.id),
        "input": {
            "name": new_promotion_name,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
        },
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionUpdate"]
    errors = data["errors"]

    assert not data["promotion"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionCreateErrorCode.INVALID.name
    assert errors[0]["field"] == "endDate"


@freeze_time("2020-03-18 12:00:00")
@patch("saleor.plugins.manager.PluginsManager.promotion_started")
@patch("saleor.plugins.manager.PluginsManager.promotion_updated")
def test_promotion_update_clears_old_sale_id(
    promotion_updated_mock,
    promotion_started_mock,
    staff_api_client,
    permission_group_manage_discounts,
    promotion_converted_from_sale,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    start_date = timezone.now() - datetime.timedelta(days=1)
    end_date = timezone.now() + datetime.timedelta(days=10)

    promotion = promotion_converted_from_sale
    assert promotion.old_sale_id
    new_promotion_name = "new test promotion"
    variables = {
        "id": graphene.Node.to_global_id("Promotion", promotion.id),
        "input": {
            "name": new_promotion_name,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
        },
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionUpdate"]
    promotion_data = data["promotion"]

    assert not data["errors"]
    assert promotion_data["name"] == new_promotion_name
    assert promotion_data["description"] == promotion.description
    assert promotion_data["startDate"] == start_date.isoformat()
    assert promotion_data["endDate"] == end_date.isoformat()
    assert promotion_data["createdAt"] == promotion.created_at.isoformat()
    assert promotion_data["updatedAt"] == timezone.now().isoformat()

    promotion.refresh_from_db()
    assert promotion.last_notification_scheduled_at == timezone.now()
    assert promotion.old_sale_id is None

    promotion_updated_mock.assert_called_once_with(promotion)
    promotion_started_mock.assert_called_once_with(promotion)
    for rule in promotion.rules.all():
        assert rule.variants_dirty is True


def test_promotion_update_events(
    staff_api_client, permission_group_manage_discounts, catalogue_promotion
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    start_date = timezone.now() - datetime.timedelta(days=1)
    end_date = timezone.now() + datetime.timedelta(days=10)

    variables = {
        "id": graphene.Node.to_global_id("Promotion", catalogue_promotion.id),
        "input": {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
        },
    }
    event_count = PromotionEvent.objects.count()

    # when
    response = staff_api_client.post_graphql(PROMOTION_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionUpdate"]
    assert not data["errors"]

    event_types = {event["type"] for event in data["promotion"]["events"]}
    assert len(event_types) == 2
    assert PromotionEvent.objects.count() == event_count + 2
    assert PromotionEvents.PROMOTION_UPDATED.upper() in event_types
    assert PromotionEvents.PROMOTION_STARTED.upper() in event_types

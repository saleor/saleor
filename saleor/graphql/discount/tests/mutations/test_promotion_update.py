from datetime import timedelta
from unittest.mock import patch

import graphene
from django.utils import timezone
from freezegun import freeze_time

from .....discount import PromotionEvents
from .....discount.error_codes import PromotionCreateErrorCode
from .....discount.models import PromotionEvent
from ....tests.utils import assert_no_permission, get_graphql_content

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
    start_date = timezone.now() - timedelta(days=1)
    end_date = timezone.now() + timedelta(days=10)

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

    end_date = timezone.now() + timedelta(days=2)

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
    promotion.last_notification_scheduled_at = timezone.now() - timedelta(hours=1)
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
    start_date = timezone.now() + timedelta(days=1)
    end_date = timezone.now() + timedelta(days=10)

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
    start_date = timezone.now() + timedelta(days=1)
    end_date = timezone.now() - timedelta(days=10)

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
    start_date = timezone.now() - timedelta(days=1)
    end_date = timezone.now() + timedelta(days=10)

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
    start_date = timezone.now() - timedelta(days=1)
    end_date = timezone.now() + timedelta(days=10)

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

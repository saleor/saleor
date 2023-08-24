import json
from decimal import Decimal

import graphene

from .....discount import PromotionEvents, RewardValueType
from .....tests.utils import dummy_editorjs
from ....tests.utils import assert_no_permission, get_graphql_content

QUERY_PROMOTION_BY_ID = """
    query Promotion($id: ID!) {
        promotion(id: $id) {
            id
            name
            description
            startDate
            endDate
            createdAt
            updatedAt
            rules {
                name
                description
                promotion {
                    id
                }
                channels {
                    slug
                }
                rewardValueType
                rewardValue
                cataloguePredicate
            }
        }
    }
"""


def _assert_promotion_data(promotion, content_data):
    promotion_data = content_data["data"]["promotion"]
    assert promotion_data["name"] == promotion.name
    assert promotion_data["description"] == promotion.description
    assert promotion_data["startDate"] == promotion.start_date.isoformat()
    assert promotion_data["endDate"] == promotion.end_date.isoformat()
    assert promotion_data["createdAt"] == promotion.created_at.isoformat()
    assert promotion_data["updatedAt"] == promotion.updated_at.isoformat()
    assert len(promotion_data["rules"]) == promotion.rules.count()
    for rule in promotion.rules.all():
        rule_data = {
            "name": rule.name,
            "description": rule.description,
            "promotion": {"id": graphene.Node.to_global_id("Promotion", promotion.id)},
            "channels": [{"slug": channel.slug} for channel in rule.channels.all()],
            "rewardValueType": rule.reward_value_type.upper(),
            "rewardValue": rule.reward_value,
            "cataloguePredicate": rule.catalogue_predicate,
        }
        assert rule_data in promotion_data["rules"]


def test_query_promotion_by_id_by_staff_user(
    promotion, staff_api_client, permission_group_manage_discounts
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)

    variables = {"id": promotion_id}

    # when
    response = staff_api_client.post_graphql(QUERY_PROMOTION_BY_ID, variables)

    # then
    content = get_graphql_content(response)
    _assert_promotion_data(promotion, content)


def test_query_promotion_by_id_by_app(
    promotion, app_api_client, permission_manage_discounts
):
    # given
    app_api_client.app.permissions.add(permission_manage_discounts)
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    variables = {"id": promotion_id}

    # when
    response = app_api_client.post_graphql(QUERY_PROMOTION_BY_ID, variables)

    # then
    content = get_graphql_content(response)
    _assert_promotion_data(promotion, content)


def test_query_promotion_by_id_by_customer(promotion, api_client):
    # given
    variables = {"id": graphene.Node.to_global_id("Promotion", promotion.id)}

    # when
    response = api_client.post_graphql(QUERY_PROMOTION_BY_ID, variables)

    # then
    assert_no_permission(response)


def test_query_promotion_without_rules_by_id(
    promotion, staff_api_client, permission_group_manage_discounts
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    promotion.rules.all().delete()

    variables = {"id": graphene.Node.to_global_id("Promotion", promotion.id)}

    # when
    response = staff_api_client.post_graphql(QUERY_PROMOTION_BY_ID, variables)

    # then
    content = get_graphql_content(response)
    _assert_promotion_data(promotion, content)


def test_query_promotion_with_complex_rule_2(
    promotion,
    staff_api_client,
    permission_group_manage_discounts,
    product,
    collection,
    category,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    promotion.rules.all().delete()
    catalogue_predicate = {
        "OR": [
            {
                "AND": [
                    {"collectionPredicate": {"ids": [collection.id]}},
                    {"categoryPredicate": {"ids": [category.id]}},
                ]
            },
            {"productPredicate": {"ids": [product.id]}},
        ]
    }
    promotion.rules.create(
        name="Percentage promotion rule",
        promotion=promotion,
        description=dummy_editorjs("Test description for percentage promotion rule."),
        catalogue_predicate=catalogue_predicate,
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=Decimal("10"),
    )

    variables = {"id": graphene.Node.to_global_id("Promotion", promotion.id)}

    # when
    response = staff_api_client.post_graphql(QUERY_PROMOTION_BY_ID, variables)

    # then
    content = get_graphql_content(response)
    _assert_promotion_data(promotion, content)


def test_query_promotion_translation(
    staff_api_client, promotion, promotion_translation_fr, permission_manage_discounts
):
    # given
    query = """
        query ($promotionId: ID!) {
            promotion(id: $promotionId) {
                translation(languageCode: FR) {
                    name
                    description
                    language {
                        code
                    }
                }
            }
        }
    """

    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)

    # when
    response = staff_api_client.post_graphql(
        query, {"promotionId": promotion_id}, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    translation_data = content["data"]["promotion"]["translation"]
    assert translation_data["name"] == promotion_translation_fr.name
    assert translation_data["description"] == dummy_editorjs(
        "French promotion description.", json_format=True
    )
    assert (
        translation_data["language"]["code"]
        == promotion_translation_fr.language_code.upper()
    )


def test_query_promotion_rule_translation(
    staff_api_client,
    promotion,
    promotion_rule_translation_fr,
    permission_manage_discounts,
):
    # given
    query = """
        query ($promotionId: ID!) {
            promotion(id: $promotionId) {
                rules {
                    id
                    translation(languageCode: FR) {
                        name
                        description
                        language {
                            code
                        }
                    }
                }
            }
        }
    """

    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)

    # when
    response = staff_api_client.post_graphql(
        query, {"promotionId": promotion_id}, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    rules = content["data"]["promotion"]["rules"]
    for rule in rules:
        if rule["id"] == graphene.Node.to_global_id(
            "PromotionRule", promotion_rule_translation_fr.promotion_rule_id
        ):
            assert rule["translation"]["name"] == promotion_rule_translation_fr.name
            assert rule["translation"]["description"] == json.dumps(
                promotion_rule_translation_fr.description
            )
            assert rule["translation"]["language"]["code"] == "FR"
        else:
            assert not rule["translation"]


QUERY_PROMOTION_BY_ID_WITH_EVENTS = """
    query Promotion($id: ID!) {
        promotion(id: $id) {
            id
            events {
                ... on PromotionEventInterface {
                    type
                    createdBy {
                        ... on User {
                            id
                        }
                    }
                }
                ... on PromotionRuleEventInterface {
                    ruleId
                }
            }
        }
    }
"""


def test_query_promotion_events(
    promotion_events,
    staff_api_client,
    permission_manage_discounts,
    permission_manage_staff,
):
    # given
    promotion = promotion_events[0].promotion
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    variables = {"id": promotion_id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PROMOTION_BY_ID_WITH_EVENTS,
        variables,
        permissions=(permission_manage_discounts, permission_manage_staff),
    )

    # then
    content = get_graphql_content(response)
    events = content["data"]["promotion"]["events"]
    assert len(events) == promotion.events.count()
    rule_events = [
        PromotionEvents.RULE_CREATED,
        PromotionEvents.RULE_UPDATED,
        PromotionEvents.RULE_DELETED,
    ]
    for db_event in promotion.events.all():
        event_data = {
            "type": db_event.type.upper(),
            "createdBy": {"id": graphene.Node.to_global_id("User", db_event.user.id)},
        }
        if db_event.type in rule_events:
            event_data["ruleId"] = db_event.parameters.get("rule_id")

        assert event_data in events

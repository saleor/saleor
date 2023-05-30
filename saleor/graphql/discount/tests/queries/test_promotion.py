from decimal import Decimal

import graphene

from .....discount import RewardValueType
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

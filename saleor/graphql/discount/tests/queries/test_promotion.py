import json

import graphene

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
                cataloguePredicate {
                    predicate {
                        ... on ProductPredicate {
                            ids
                            __typename
                        }
                        ... on ProductVariantPredicate {
                            ids
                            __typename
                        }
                        ... on CategoryPredicate {
                            ids
                            __typename
                        }
                        ... on CollectionPredicate {
                            ids
                            __typename
                        }
                    }
                }
            }
        }
    }
"""


def _assert_promotion_data(promotion, content_data):
    promotion_data = content_data["data"]["promotion"]
    assert promotion_data["name"] == promotion.name
    assert promotion_data["description"] == json.dumps(promotion.description)
    assert promotion_data["startDate"] == promotion.start_date.isoformat()
    assert promotion_data["endDate"] == promotion.end_date.isoformat()
    assert promotion_data["createdAt"] == promotion.created_at.isoformat()
    assert promotion_data["updatedAt"] == promotion.updated_at.isoformat()
    assert len(promotion_data["rules"]) == promotion.rules.count()
    for rule in promotion.rules.all():
        rule_data = {
            "name": rule.name,
            "description": json.dumps(rule.description),
            "promotion": {"id": graphene.Node.to_global_id("Promotion", promotion.id)},
            "channels": [{"slug": channel.slug} for channel in rule.channels.all()],
            "rewardValueType": rule.reward_value_type.upper(),
            "rewardValue": rule.reward_value,
            "cataloguePredicate": {
                "predicate": _prepare_simple_predicate_data(rule.catalogue_predicate)
            },
        }
        assert rule_data in promotion_data["rules"]


def _prepare_simple_predicate_data(predicate):
    if not predicate:
        return None
    for model_name in ["Product", "Category", "Collection"]:
        if data := predicate.get(f"{model_name.lower()}Predicate"):
            return {
                "__typename": f"{model_name}Predicate",
                "ids": [
                    graphene.Node.to_global_id(model_name, id) for id in data.get("ids")
                ],
            }
    if data := predicate.get("variantPredicate"):
        return {
            "__typename": "ProductVariantPredicate",
            "ids": [
                graphene.Node.to_global_id("ProductVariant", id)
                for id in data.get("ids")
            ],
        }


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


# TODO: check the rule with more complex predicate

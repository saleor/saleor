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
                rewardValue
            }
        }
    }
"""


def test_query_promotion_by_id_by_staff_user(
    promotion, staff_api_client, permission_group_manage_discounts
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    variables = {"id": graphene.Node.to_global_id("Promotion", promotion.id)}

    # when
    response = staff_api_client.post_graphql(QUERY_PROMOTION_BY_ID, variables)

    # then
    content = get_graphql_content(response)
    sale_data = content["data"]["promotion"]

    # TODO: add validation
    assert sale_data


def test_query_promotion_by_id_by_app(
    promotion, staff_api_client, permission_group_manage_discounts
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    variables = {"id": graphene.Node.to_global_id("Promotion", promotion.id)}

    # when
    response = staff_api_client.post_graphql(QUERY_PROMOTION_BY_ID, variables)

    # then
    content = get_graphql_content(response)
    sale_data = content["data"]["promotion"]
    assert sale_data
    # TODO: add validation


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

    variables = {"id": graphene.Node.to_global_id("Promotion", promotion.id)}

    # when
    response = staff_api_client.post_graphql(QUERY_PROMOTION_BY_ID, variables)

    # then
    content = get_graphql_content(response)
    sale_data = content["data"]["promotion"]
    assert sale_data
    # TODO: add validation


# TODO: check the rule with more complex predicate

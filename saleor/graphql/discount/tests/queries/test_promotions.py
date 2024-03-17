from datetime import timedelta

from django.utils import timezone

from ....tests.utils import assert_no_permission, get_graphql_content

QUERY_PROMOTIONS = """
    query {
        promotions(first: 10) {
            edges {
                node {
                    id
                    name
                    description
                    startDate
                    rules {
                        id
                    }
                }
            }
        }
    }
"""


def test_query_promotions_by_staff_user(
    promotion_list, staff_api_client, permission_manage_discounts
):
    # given
    variables = {}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PROMOTIONS, variables, permissions=(permission_manage_discounts,)
    )

    # then
    content = get_graphql_content(response)
    promotions = content["data"]["promotions"]["edges"]
    assert len(promotions) == len(promotion_list)
    assert promotions[0]["node"]["name"] == promotion_list[0].name
    assert promotions[0]["node"]["description"] == promotion_list[0].description
    assert (
        promotions[0]["node"]["startDate"] == promotion_list[0].start_date.isoformat()
    )
    assert len(promotions[0]["node"]["rules"]) == len(promotion_list[0].rules.all())


def test_query_promotions_by_app(
    promotion_list, app_api_client, permission_manage_discounts
):
    # given
    variables = {}

    # when
    response = app_api_client.post_graphql(
        QUERY_PROMOTIONS, variables, permissions=(permission_manage_discounts,)
    )

    # then
    content = get_graphql_content(response)
    promotions = content["data"]["promotions"]["edges"]
    assert len(promotions) == len(promotion_list)
    assert promotions[0]["node"]["name"] == promotion_list[0].name
    assert promotions[0]["node"]["description"] == promotion_list[0].description
    assert (
        promotions[0]["node"]["startDate"] == promotion_list[0].start_date.isoformat()
    )
    assert len(promotions[0]["node"]["rules"]) == len(promotion_list[0].rules.all())


def test_query_promotions_by_customer(
    promotion_list, api_client, permission_manage_discounts
):
    # given
    variables = {}

    # when
    response = api_client.post_graphql(QUERY_PROMOTIONS, variables)

    # then
    assert_no_permission(response)


QUERY_PROMOTIONS_PAGINATION = """
    query Promotions(
        $first: Int, $last: Int, $after: String, $before: String,
        $where: PromotionWhereInput, $sortBy: PromotionSortingInput
    ){
        promotions(
            first: $first, last: $last, after: $after, before: $before,
            where: $where, sortBy: $sortBy
        ) {
            edges {
                node {
                    id
                    name
                }
            }
            pageInfo{
                startCursor
                endCursor
                hasNextPage
                hasPreviousPage
            }
        }
    }
"""


def test_query_promotions_pagination(
    promotion_list, catalogue_promotion, staff_api_client, permission_manage_discounts
):
    # given
    end_cursor = None
    has_next_page = True
    object_count = 0
    queries_count = 0
    names = []

    variables = {
        "first": 2,
        "after": None,
        "sortBy": {
            "direction": "DESC",
            "field": "NAME",
        },
        "where": {
            "endDate": {
                "range": {
                    "gte": timezone.now() + timedelta(days=15),
                }
            }
        },
    }

    # when
    while has_next_page:
        variables["after"] = end_cursor
        response = staff_api_client.post_graphql(
            QUERY_PROMOTIONS_PAGINATION,
            variables,
            check_no_permissions=False,
            permissions=(permission_manage_discounts,),
        )
        content = get_graphql_content(response)
        promotions = content["data"]["promotions"]
        page_info = promotions["pageInfo"]
        has_next_page = page_info["hasNextPage"]
        end_cursor = page_info["endCursor"]

        queries_count += 1
        object_count += len(promotions["edges"])
        names.extend(promotion["node"]["name"] for promotion in promotions["edges"])

    # then
    assert object_count == 3
    assert queries_count == 2
    assert promotion_list[0].name not in names

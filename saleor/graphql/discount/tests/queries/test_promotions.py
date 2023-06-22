from datetime import timedelta

import graphene
import pytest
from django.utils import timezone

from ....tests.utils import assert_no_permission, get_graphql_content

QUERY_PROMOTIONS = """
    query Promotions($where: PromotionWhereInput, $sortBy: PromotionSortingInput){
        promotions(first: 10, where: $where, sortBy: $sortBy) {
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


def test_query_promotions_filter_by_id(
    promotion_list, staff_api_client, permission_manage_discounts
):
    # given
    ids = [
        graphene.Node.to_global_id("Promotion", promotion.pk)
        for promotion in promotion_list[:2]
    ]
    variables = {"where": {"ids": ids}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PROMOTIONS, variables, permissions=(permission_manage_discounts,)
    )

    # then
    content = get_graphql_content(response)
    promotions = content["data"]["promotions"]["edges"]
    assert len(promotions) == 2
    names = {node["node"]["name"] for node in promotions}
    assert names == {promotion_list[0].name, promotion_list[1].name}


def test_query_promotions_filter_by_name(
    promotion_list, staff_api_client, permission_manage_discounts
):
    # given
    variables = {"where": {"name": {"oneOf": ["Promotion 1", "Promotion 3"]}}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PROMOTIONS, variables, permissions=(permission_manage_discounts,)
    )

    # then
    content = get_graphql_content(response)
    promotions = content["data"]["promotions"]["edges"]
    assert len(promotions) == 2
    names = {node["node"]["name"] for node in promotions}
    assert names == {promotion_list[0].name, promotion_list[2].name}


def test_query_promotions_filter_by_end_date(
    promotion_list, staff_api_client, permission_manage_discounts
):
    # given
    variables = {
        "where": {
            "endDate": {
                "gte": timezone.now() + timedelta(days=5),
                "lte": timezone.now() + timedelta(days=25),
            }
        },
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PROMOTIONS, variables, permissions=(permission_manage_discounts,)
    )

    # then
    content = get_graphql_content(response)
    promotions = content["data"]["promotions"]["edges"]
    assert len(promotions) == 2
    names = {node["node"]["name"] for node in promotions}
    assert names == {promotion_list[0].name, promotion_list[1].name}


def test_query_promotions_filter_by_start_date(
    promotion_list, staff_api_client, permission_manage_discounts
):
    # given
    variables = {
        "where": {
            "startDate": {
                "gte": timezone.now() + timedelta(days=3),
            }
        },
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PROMOTIONS, variables, permissions=(permission_manage_discounts,)
    )

    # then
    content = get_graphql_content(response)
    promotions = content["data"]["promotions"]["edges"]
    assert len(promotions) == 2
    names = {node["node"]["name"] for node in promotions}
    assert names == {promotion_list[1].name, promotion_list[2].name}


@pytest.mark.parametrize("value,indexes", [(True, [0]), (False, [1, 2])])
def test_query_promotions_filter_by_is_old_sale(
    value, indexes, promotion_list, staff_api_client, permission_manage_discounts
):
    # given
    promotion_list[0].old_sale = True
    promotion_list[0].save(update_fields=["old_sale"])
    variables = {"where": {"isOldSale": value}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PROMOTIONS, variables, permissions=(permission_manage_discounts,)
    )

    # then
    content = get_graphql_content(response)
    promotions = content["data"]["promotions"]["edges"]
    assert len(promotions) == len(indexes)
    assert {promotion_list[index].name for index in indexes} == {
        promotion["node"]["name"] for promotion in promotions
    }


@pytest.mark.parametrize("direction", ("ASC", "DESC"))
def test_sorting_promotions_by_name(
    direction,
    staff_api_client,
    promotion,
    promotion_list,
    permission_manage_discounts,
):
    # given
    promotion_list.insert(0, promotion)
    variables = {
        "sortBy": {
            "direction": direction,
            "field": "NAME",
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PROMOTIONS, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    promotions = content["data"]["promotions"]["edges"]
    if direction == "DESC":
        promotions.reverse()
    assert len(promotions) == 4
    assert [promotion["node"]["name"] for promotion in promotions] == [
        promotion.name for promotion in promotion_list
    ]


@pytest.mark.parametrize("direction", ("ASC", "DESC"))
def test_sorting_promotions_by_end_date(
    direction,
    staff_api_client,
    promotion,
    promotion_list,
    permission_manage_discounts,
):
    # given
    promotion_list.insert(2, promotion)
    variables = {
        "sortBy": {
            "direction": direction,
            "field": "END_DATE",
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PROMOTIONS, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    promotions = content["data"]["promotions"]["edges"]
    if direction == "DESC":
        promotions.reverse()
    assert len(promotions) == 4
    assert [promotion["node"]["name"] for promotion in promotions] == [
        promotion.name for promotion in promotion_list
    ]


@pytest.mark.parametrize("direction", ("ASC", "DESC"))
def test_sorting_promotions_by_start_date(
    direction,
    staff_api_client,
    promotion,
    promotion_list,
    permission_manage_discounts,
):
    # given
    promotion.start_date = timezone.now() + timedelta(days=3)
    promotion.save(update_fields=["start_date"])
    promotion_list.insert(1, promotion)
    variables = {
        "sortBy": {
            "direction": direction,
            "field": "START_DATE",
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PROMOTIONS, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    promotions = content["data"]["promotions"]["edges"]
    if direction == "DESC":
        promotions.reverse()
    assert len(promotions) == 4
    assert [promotion["node"]["name"] for promotion in promotions] == [
        promotion.name for promotion in promotion_list
    ]


@pytest.mark.parametrize("direction", ("ASC", "DESC"))
def test_sorting_promotions_by_created_at(
    direction,
    staff_api_client,
    promotion_list,
    permission_manage_discounts,
):
    # given
    variables = {
        "sortBy": {
            "direction": direction,
            "field": "CREATED_AT",
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PROMOTIONS, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    promotions = content["data"]["promotions"]["edges"]
    if direction == "DESC":
        promotions.reverse()
    assert len(promotions) == 3
    assert [promotion["node"]["name"] for promotion in promotions] == [
        promotion.name for promotion in promotion_list
    ]


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
    promotion_list, promotion, staff_api_client, permission_manage_discounts
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
                "gte": timezone.now() + timedelta(days=15),
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

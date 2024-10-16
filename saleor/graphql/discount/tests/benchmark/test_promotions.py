import pytest

from ....tests.utils import get_graphql_content

PROMOTIONS_QUERY = """
query {
    promotions(first: 10) {
        edges {
            node {
                id
                name
                description
                startDate
                endDate
                createdAt
                updatedAt
                rules {
                    id
                    name
                    description
                    channels {
                        id
                        slug
                    }
                    rewardValueType
                    rewardValue
                    cataloguePredicate
                    translation(languageCode: PL) {
                        name
                    }
                }
                translation(languageCode: PL) {
                    name
                }
            }
        }
    }
}
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_promotions_querytest_promotions_query(
    staff_api_client,
    promotion_list_for_benchmark,
    permission_group_manage_discounts,
    count_queries,
):
    # given
    staff_api_client.user.groups.add(permission_group_manage_discounts)

    # when
    content = get_graphql_content(
        staff_api_client.post_graphql(
            PROMOTIONS_QUERY,
            {},
        )
    )

    # then
    data = content["data"]["promotions"]
    assert data

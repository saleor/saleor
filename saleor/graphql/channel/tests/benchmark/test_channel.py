import pytest

from ....tests.utils import get_graphql_content

CHANNELS_QUERY = """
    query {
        channels {
            name
            slug
            currencyCode
            warehouses {
                id
            }
            defaultCountry {
                code
                country
            }
        }
    }
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_channels_query(
    staff_api_client, permission_manage_channels, channels_for_benchmark, count_queries
):
    content = get_graphql_content(
        staff_api_client.post_graphql(
            CHANNELS_QUERY,
            permissions=[permission_manage_channels],
            check_no_permissions=False,
        )
    )

    assert content["data"]["channels"]

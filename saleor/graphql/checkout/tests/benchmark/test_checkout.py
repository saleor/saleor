import pytest

from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

CHECKOUT_DETAILS_QUERY = """
query checkout($id: ID){
  checkout(
		id:$id
	) {
		shippingMethods{
			active
			message
		}
		lines{
			id
			variant{
				product{
					name
				}
			}
			totalPrice{
				gross{
					amount
				}
				net{
					amount
				}
			}
		}
		totalPrice{
			gross{
				amount
			}
		}
		subtotalPrice{
			gross{
				amount
			}
		}
		shippingPrice{
			net{
				amount
			}
			gross{
				amount
			}
		}

  }
}
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_user_checkout_details(
    user_api_client,
    checkouts_for_benchmarks,
    count_queries,
):
    # given
    checkout = checkouts_for_benchmarks[0]
    checkout_id = to_global_id_or_none(checkout)

    # when
    content = get_graphql_content(
        user_api_client.post_graphql(
            CHECKOUT_DETAILS_QUERY, variables={"id": checkout_id}
        )
    )

    # then
    assert content["data"]["checkout"] is not None

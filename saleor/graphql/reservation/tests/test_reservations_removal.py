import graphene

from ....reservation.models import Reservation
from ...tests.utils import get_graphql_content

MUTATION_RESERVATIONS_REMOVE = """
    mutation removeReservations($reservationInput: ReservationsRemoveInput!) {
      reservationsRemove(input: $reservationInput) {
        reservationsErrors {
          field
          message
          code
        }
      }
    }
"""


def test_mutation_removes_stock_reservations(
    customer_user, user_api_client, variant_with_reserved_stock
):
    variant = variant_with_reserved_stock
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "reservationInput": {
            "countryCode": "US",
            "variantsIds": [variant_id],
        }
    }
    assert Reservation.objects.exists()
    response = user_api_client.post_graphql(MUTATION_RESERVATIONS_REMOVE, variables)
    content = get_graphql_content(response)
    data = content["data"]["reservationsRemove"]
    assert not data["reservationsErrors"]
    assert not Reservation.objects.exists()

import graphene

from ....reservation.models import Reservation
from ...tests.utils import get_graphql_content
from ..mutations import RESERVATIONS_TO_REMOVE_LIMIT

MUTATION_RESERVATIONS_REMOVE = """
    mutation removeReservations($reservationsInput: ReservationsRemoveInput!) {
      reservationsRemove(input: $reservationsInput) {
        removedReservations {
            productVariant {
                id
            }
            quantity
        }
        reservationsErrors {
          field
          message
          code
        }
      }
    }
"""


def test_mutation_removes_users_stock_reservations(
    customer_user, user_api_client, variant_with_reserved_stock
):
    variant = variant_with_reserved_stock
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "reservationsInput": {
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

    assert data["removedReservations"] == [
        {
            "productVariant": {"id": variant_id},
            "quantity": 3,
        }
    ]


def test_mutation_fails_if_invalid_products_variants_are_given(
    customer_user, user_api_client, variant_with_reserved_stock
):
    variant = variant_with_reserved_stock
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id + 10)
    variables = {
        "reservationsInput": {
            "countryCode": "US",
            "variantsIds": [variant_id],
        }
    }
    assert Reservation.objects.exists()
    response = user_api_client.post_graphql(MUTATION_RESERVATIONS_REMOVE, variables)
    content = get_graphql_content(response)
    data = content["data"]["reservationsRemove"]
    assert data["reservationsErrors"][0]["message"] == (
        "Could not resolve to a node with the global id list "
        "of '{'%s'}'." % variant_id
    )
    assert Reservation.objects.exists()


def test_mutation_fails_if_too_many_reservations_to_delete_are_given(
    customer_user, user_api_client, variant_with_reserved_stock
):
    variants_ids = [
        graphene.Node.to_global_id("ProductVariant", i + 1)
        for i in range(RESERVATIONS_TO_REMOVE_LIMIT + 1)
    ]
    variables = {
        "reservationsInput": {
            "countryCode": "US",
            "variantsIds": variants_ids,
        }
    }
    assert Reservation.objects.exists()
    response = user_api_client.post_graphql(MUTATION_RESERVATIONS_REMOVE, variables)
    content = get_graphql_content(response)
    data = content["data"]["reservationsRemove"]
    assert data["reservationsErrors"][0]["message"] == (
        "Cannot remove more than 50 reservations at once."
    )
    assert Reservation.objects.exists()


def test_mutation_fails_if_user_is_not_authenticated(
    api_client, variant_with_reserved_stock
):
    variant = variant_with_reserved_stock
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "reservationsInput": {
            "countryCode": "US",
            "variantsIds": [variant_id],
        }
    }
    assert Reservation.objects.exists()
    response = api_client.post_graphql(MUTATION_RESERVATIONS_REMOVE, variables)
    content = get_graphql_content(response, ignore_errors=True)
    assert content["errors"][0]["message"] == (
        "You do not have permission to perform this action"
    )
    assert Reservation.objects.exists()

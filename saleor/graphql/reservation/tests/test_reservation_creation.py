import graphene

from ....reservation.models import Reservation
from ...tests.utils import get_graphql_content

MUTATION_RESERVATION_CREATE = """
    mutation createReservation($reservationInput: ReservationCreateInput!) {
      reservationCreate(input: $reservationInput) {
        reservation {
            quantity
        }
        reservationErrors {
          field
          message
          code
        }
      }
    }
"""


def test_mutation_creates_new_stock_reservation(
    customer_user, user_api_client, variant_with_many_stocks
):
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "reservationInput": {
            "countryCode": "US",
            "quantity": 4,
            "variantId": variant_id,
        }
    }
    assert not Reservation.objects.exists()
    response = user_api_client.post_graphql(MUTATION_RESERVATION_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["reservationCreate"]
    assert not data["reservationErrors"]

    reservation = Reservation.objects.first()
    assert reservation.user == customer_user
    assert reservation.product_variant == variant_with_many_stocks
    assert reservation.quantity == 4
    assert "US" in reservation.shipping_zone.countries


def test_mutation_updates_existing_stock_reservation(
    customer_user, user_api_client, variant_with_reserved_stock
):
    variant = variant_with_reserved_stock
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "reservationInput": {
            "countryCode": "US",
            "quantity": 2,
            "variantId": variant_id,
        }
    }
    reservation = Reservation.objects.first()
    assert reservation.quantity == 3
    response = user_api_client.post_graphql(MUTATION_RESERVATION_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["reservationCreate"]
    assert not data["reservationErrors"]

    reservation.refresh_from_db()
    assert reservation.quantity == 2


def test_mutation_updates_expired_stock_reservation(
    customer_user, user_api_client, variant_with_expired_stock_reservation
):
    variant = variant_with_expired_stock_reservation
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "reservationInput": {
            "countryCode": "US",
            "quantity": 2,
            "variantId": variant_id,
        }
    }
    expired_reservation = Reservation.objects.first()
    assert expired_reservation
    response = user_api_client.post_graphql(MUTATION_RESERVATION_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["reservationCreate"]
    assert not data["reservationErrors"]

    reservation = Reservation.objects.first()
    assert reservation == expired_reservation
    assert reservation.expires > expired_reservation.expires


def test_mutation_fails_if_user_is_not_authenticated(
    api_client, variant_with_many_stocks
):
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "reservationInput": {
            "countryCode": "US",
            "quantity": 2,
            "variantId": variant_id,
        }
    }
    assert not Reservation.objects.exists()
    response = api_client.post_graphql(MUTATION_RESERVATION_CREATE, variables)
    content = get_graphql_content(response, ignore_errors=True)
    assert content["errors"][0]["message"] == (
        "You do not have permission to perform this action"
    )
    assert not Reservation.objects.exists()


def test_mutation_fails_when_reserved_quantity_is_less_than_one(
    user_api_client, variant_with_many_stocks
):
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "reservationInput": {
            "countryCode": "US",
            "quantity": 0,
            "variantId": variant_id,
        }
    }
    assert not Reservation.objects.exists()
    response = user_api_client.post_graphql(MUTATION_RESERVATION_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["reservationCreate"]
    assert data["reservationErrors"][0]["message"] == (
        "The quantity should be higher than zero."
    )
    assert not Reservation.objects.exists()


def test_mutation_fails_when_reserved_quantity_exceeds_limit(
    user_api_client, variant_with_many_stocks
):
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "reservationInput": {
            "countryCode": "US",
            "quantity": 2000,
            "variantId": variant_id,
        }
    }
    assert not Reservation.objects.exists()
    response = user_api_client.post_graphql(MUTATION_RESERVATION_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["reservationCreate"]
    assert data["reservationErrors"][0]["message"] == (
        "Cannot reserve more than 50 times this item."
    )
    assert not Reservation.objects.exists()


def test_mutation_fails_when_reserved_quantity_exceeds_available_quantity(
    user_api_client, variant_with_many_stocks
):
    variant = variant_with_many_stocks
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "reservationInput": {
            "countryCode": "US",
            "quantity": 40,
            "variantId": variant_id,
        }
    }
    assert not Reservation.objects.exists()
    response = user_api_client.post_graphql(MUTATION_RESERVATION_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["reservationCreate"]
    assert data["reservationErrors"][0]["message"] == (
        "Could not reserve item Test product (SKU_A). Only 7 remain in stock."
    )
    assert not Reservation.objects.exists()


def test_mutation_fails_when_variant_could_not_be_found(user_api_client):
    variant_id = graphene.Node.to_global_id("ProductVariant", 1)
    variables = {
        "reservationInput": {
            "countryCode": "JP",
            "quantity": 5,
            "variantId": variant_id,
        }
    }
    assert not Reservation.objects.exists()
    response = user_api_client.post_graphql(MUTATION_RESERVATION_CREATE, variables)
    content = get_graphql_content(response)
    data = content["data"]["reservationCreate"]
    assert data["reservationErrors"][0]["message"] == (
        "Couldn't resolve to a node: UHJvZHVjdFZhcmlhbnQ6MQ=="
    )
    assert not Reservation.objects.exists()

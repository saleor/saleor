from ..stock import (
    get_reserved_quantity,
    get_reserved_quantity_bulk,
    get_user_reserved_quantity_bulk,
    remove_expired_reservations,
    remove_user_reservations,
)

COUNTRY_CODE = "US"


def test_zero_reservations_are_returned_for_variant_without_any_reservations(variant):
    assert get_reserved_quantity(variant, COUNTRY_CODE) == 0


def test_reserved_quantity_is_returned_for_variant_with_reservations(
    variant_with_reserved_stock,
):
    assert get_reserved_quantity(variant_with_reserved_stock, COUNTRY_CODE) == 3


def test_reserved_quantity_excludes_user_reservations(
    variant_with_reserved_stock, customer_user
):
    assert (
        get_reserved_quantity(variant_with_reserved_stock, COUNTRY_CODE, customer_user)
        == 0
    )


def test_reserved_quantity_excludes_expired_reservations(
    variant_with_expired_stock_reservation,
):
    assert (
        get_reserved_quantity(variant_with_expired_stock_reservation, COUNTRY_CODE) == 0
    )


def test_reservations_can_be_retrieved_in_bulk(variant_with_reserved_stock):
    reservations = get_reserved_quantity_bulk(
        [variant_with_reserved_stock], COUNTRY_CODE
    )
    assert reservations[variant_with_reserved_stock.id] == 3


def test_bulk_reservations_retrieval_excludes_user_reservations(
    variant_with_reserved_stock, customer_user
):
    reservations = get_reserved_quantity_bulk(
        [variant_with_reserved_stock], COUNTRY_CODE, customer_user
    )
    assert reservations[variant_with_reserved_stock.id] == 0


def test_bulk_reservations_retrieval_excludes_expired_reservations(
    variant_with_expired_stock_reservation,
):
    reservations = get_reserved_quantity_bulk(
        [variant_with_expired_stock_reservation], COUNTRY_CODE
    )
    assert reservations[variant_with_expired_stock_reservation.id] == 0


def test_user_reservations_can_be_retrieved_in_bulk(
    variant_with_reserved_stock, customer_user
):
    reservations = get_user_reserved_quantity_bulk(
        customer_user, COUNTRY_CODE, [variant_with_reserved_stock]
    )
    assert reservations[variant_with_reserved_stock.id] == 3


def test_user_reservations_exclude_other_users_reservations(
    variant_with_reserved_stock, staff_user
):
    reservations = get_user_reserved_quantity_bulk(
        staff_user, COUNTRY_CODE, [variant_with_reserved_stock]
    )
    assert reservations[variant_with_reserved_stock.id] == 0


def test_user_reservations_exclude_expired_reservations(
    variant_with_expired_stock_reservation, customer_user
):
    reservations = get_user_reserved_quantity_bulk(
        customer_user, COUNTRY_CODE, [variant_with_expired_stock_reservation]
    )
    assert reservations[variant_with_expired_stock_reservation.id] == 0


def test_user_reservations_are_removed(variant_with_reserved_stock, customer_user):
    remove_user_reservations(customer_user, COUNTRY_CODE, [variant_with_reserved_stock])
    reservations = get_reserved_quantity_bulk(
        [variant_with_reserved_stock], COUNTRY_CODE, customer_user
    )
    assert reservations[variant_with_reserved_stock.id] == 0

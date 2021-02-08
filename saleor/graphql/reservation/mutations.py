from datetime import datetime, timedelta
from typing import TYPE_CHECKING, List, TypedDict

import graphene
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from ...core.exceptions import InsufficientStock
from ...reservation.error_codes import ReservationErrorCode
from ...reservation import models
from ...reservation.stock import (
    get_user_reserved_quantity_bulk,
    remove_user_reservations,
)
from ...warehouse.availability import check_stock_quantity
from ...shipping.models import ShippingZone
from ..account.enums import CountryCodeEnum
from ..core.mutations import BaseMutation
from ..core.types.common import ReservationError
from ..product.types import ProductVariant
from .types import RemovedReservation, Reservation

if TYPE_CHECKING:
    from ...account.models import User

RESERVATION_LENGTH = timedelta(minutes=10)
RESERVATION_SIZE_LIMIT = settings.MAX_CHECKOUT_LINE_QUANTITY
RESERVATIONS_TO_REMOVE_LIMIT = 50


def _get_reservation_expiration() -> "datetime":
    return timezone.now() + RESERVATION_LENGTH


def check_reservation_quantity(
    user: "User",
    product_variant: "ProductVariant",
    country_code: str,
    quantity: int,
):
    """Check if reservation for given quantity is allowed."""
    if quantity < 1:
        raise ValidationError(
            {
                "quantity": ValidationError(
                    "The quantity should be higher than zero.",
                    code=ReservationErrorCode.ZERO_QUANTITY,
                )
            }
        )
    if quantity > RESERVATION_SIZE_LIMIT:
        raise ValidationError(
            {
                "quantity": ValidationError(
                    "Cannot reserve more than %d times this item."
                    "" % RESERVATION_SIZE_LIMIT,
                    code=ReservationErrorCode.QUANTITY_GREATER_THAN_LIMIT,
                )
            }
        )

    try:
        check_stock_quantity(
            product_variant,
            country_code,
            quantity,
            user,
        )
    except InsufficientStock as e:
        remaining = e.context["available_quantity"]
        item_name = e.item.display_product()
        message = (
            f"Could not reserve item {item_name}. Only {remaining} remaining in stock."
        )
        raise ValidationError({"quantity": ValidationError(message, code=e.code)})


@transaction.atomic
def reserve_stock_for_user(
    user: "User", country_code: str, quantity: int, product_variant: "ProductVariant"
) -> "Reservation":
    """Reserve stock of given product variant for the user.

    Function lock for update all reservations for variant and user. Next, create or
    update quantity of existing reservation for the user.
    """
    reservation = (
        models.Reservation.objects.select_for_update(of=("self",))
        .filter(user=user, product_variant=product_variant)
        .first()
    )

    shipping_zone = ShippingZone.objects.filter(
        countries__contains=country_code
    ).first()

    if not shipping_zone:
        raise ValidationError(
            {
                "country_code": ValidationError(
                    "Cannot reserve stock for %d country code." "" % country_code,
                    code=ReservationErrorCode.INVALID_COUNTRY_CODE,
                )
            }
        )

    if reservation:
        reservation.shipping_zone = shipping_zone
        reservation.quantity = quantity
        reservation.expires = _get_reservation_expiration()
        reservation.save(update_fields=["shipping_zone", "quantity", "expires"])
    else:
        reservation = models.Reservation.objects.create(
            user=user,
            shipping_zone=shipping_zone,
            quantity=quantity,
            product_variant=product_variant,
            expires=_get_reservation_expiration(),
        )

    return reservation


class ReservationCreateInput(graphene.InputObjectType):
    country_code = CountryCodeEnum(description="Country code.", required=True)
    quantity = graphene.Int(
        required=True, description="The number of items to reserve."
    )
    variant_id = graphene.ID(required=True, description="ID of the product variant.")


class ReservationCreate(BaseMutation):
    reservation = graphene.Field(
        Reservation, description="An reservation instance that was created or updated."
    )

    class Arguments:
        input = ReservationCreateInput(
            required=True, description="Fields required to create reservation."
        )

    class Meta:
        description = "Reserve the stock for authenticated user checkout."
        error_type_class = ReservationError
        error_type_field = "reservation_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated

    @classmethod
    def perform_mutation(cls, root, info, **data):
        input_data = data["input"]
        product_variant = cls.get_node_or_error(
            info, input_data["variant_id"], ProductVariant
        )
        check_reservation_quantity(
            info.context.user,
            product_variant,
            input_data["country_code"],
            input_data["quantity"],
        )

        reservation = reserve_stock_for_user(
            info.context.user,
            input_data["country_code"],
            input_data["quantity"],
            product_variant,
        )

        return ReservationCreate(reservation=reservation)


class RemovedReservationDict(TypedDict):
    product_variant: ProductVariant
    quantity: int


@transaction.atomic()
def remove_reservations(
    user: "User",
    country_code: str,
    products_variants: List[ProductVariant],
) -> List[RemovedReservationDict]:
    reservations = get_user_reserved_quantity_bulk(
        user, country_code, products_variants
    )
    remove_user_reservations(user, country_code, products_variants)

    removed_reservations = []
    for variant in products_variants:
        removed_reservations.append(
            {
                "product_variant": variant,
                "quantity": reservations[variant.id],
            }
        )

    return removed_reservations


class ReservationsRemoveInput(graphene.InputObjectType):
    country_code = CountryCodeEnum(description="Country code.", required=True)
    variants_ids = graphene.List(
        graphene.ID,
        description="A list of IDs of products variants reservations to remove.",
        required=True,
    )


class ReservationsRemove(BaseMutation):
    removed_reservations = graphene.List(
        RemovedReservation, description="List of removed reservations."
    )

    class Arguments:
        input = ReservationsRemoveInput(
            required=True, description="Fields required to remove reservations."
        )

    class Meta:
        description = "Remove stock reservations made for the user."
        error_type_class = ReservationError
        error_type_field = "reservations_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated

    @classmethod
    def perform_mutation(cls, root, info, **data):
        input_data = data["input"]

        products_variants = cls.get_nodes_or_error(
            input_data["variants_ids"], ProductVariant
        )

        removed_reservations = remove_reservations(
            info.context.user, input_data["country_code"], products_variants
        )

        return ReservationsRemove(removed_reservations=removed_reservations)

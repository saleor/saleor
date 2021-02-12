from datetime import datetime, timedelta
from typing import TYPE_CHECKING, List, TypedDict

import graphene
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from graphql.error import GraphQLError

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
    def check_reservation_quantity(
        cls,
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
                f"Could not reserve item {item_name}. Only {remaining} remain in stock."
            )
            raise ValidationError({"quantity": ValidationError(message, code=e.code)})

    @classmethod
    def retrieve_shipping_zone(cls, country_code: str) -> ShippingZone:
        shipping_zone = ShippingZone.objects.filter(
            countries__contains=country_code
        ).first()

        if not shipping_zone:
            raise ValidationError(
                {
                    "country_code": ValidationError(
                        f"Cannot reserve stock for {country_code} country code.",
                        code=ReservationErrorCode.INVALID_COUNTRY_CODE,
                    )
                }
            )

        return shipping_zone

    @classmethod
    def clean_input(cls, info, data):
        cleaned_input = {
            "product_variant": cls.get_node_or_error(
                info, data["variant_id"], ProductVariant
            ),
            "shipping_zone": cls.retrieve_shipping_zone(data["country_code"]),
        }

        cls.check_reservation_quantity(
            info.context.user,
            cleaned_input["product_variant"],
            data["country_code"],
            data["quantity"],
        )

        cleaned_input["quantity"] = data["quantity"]
        return cleaned_input

    @classmethod
    @transaction.atomic
    def save(cls, info, cleaned_input) -> "Reservation":
        """Reserve stock of given product variant for the user.

        Function lock for update all reservations for variant and user. Next, create or
        update quantity of existing reservation for the user.
        """
        reservation = (
            models.Reservation.objects.select_for_update(of=("self",))
            .filter(
                user=info.context.user, product_variant=cleaned_input["product_variant"]
            )
            .first()
        )

        if reservation:
            reservation.shipping_zone = cleaned_input["shipping_zone"]
            reservation.quantity = cleaned_input["quantity"]
            reservation.expires = _get_reservation_expiration()
            reservation.save(update_fields=["shipping_zone", "quantity", "expires"])
        else:
            reservation = models.Reservation.objects.create(
                user=info.context.user,
                shipping_zone=cleaned_input["shipping_zone"],
                quantity=cleaned_input["quantity"],
                product_variant=cleaned_input["product_variant"],
                expires=_get_reservation_expiration(),
            )

        return reservation

    @classmethod
    def perform_mutation(cls, root, info, **data):
        cleaned_input = cls.clean_input(info, data["input"])
        instance = cls.save(info, cleaned_input)
        return ReservationCreate(reservation=instance)


class RemovedReservationDict(TypedDict):
    product_variant: ProductVariant
    quantity: int


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
        description = "Remove stock reservations made by the user."
        error_type_class = ReservationError
        error_type_field = "reservations_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated

    @classmethod
    def clean_products_variants(cls, variants_ids):
        clean_variants_ids = set(variants_ids)
        if len(clean_variants_ids) > RESERVATIONS_TO_REMOVE_LIMIT:
            raise ValidationError(
                {
                    "variants_ids": ValidationError(
                        "Cannot remove more than %s reservations at once."
                        "" % RESERVATIONS_TO_REMOVE_LIMIT,
                        code=ReservationErrorCode.TOO_MANY_RESERVATIONS,
                    )
                }
            )

        # get_nodes_or_error has logic for raising GraphQL error, the
        # underlying `get_nodes` utility raises AssertionError when only some
        # of requested IDs aren't found.
        # Likewise get_nodes_or_error can raise ValidationError with code being
        # "graphql_error" which is not something we want.
        # TODO: cleanup after get_nodes_or_error is fixed
        try:
            return cls.get_nodes_or_error(
                clean_variants_ids, "variants_ids", ProductVariant
            )
        except (AssertionError, GraphQLError) as e:
            raise ValidationError(
                {
                    "variants_ids": ValidationError(
                        str(e), code=ReservationErrorCode.NOT_FOUND
                    )
                }
            )

    @classmethod
    def clean_input(cls, data):
        return {
            "country_code": data["country_code"],
            "products_variants": cls.clean_products_variants(data["variants_ids"]),
        }

    @classmethod
    def delete(cls, info, cleaned_input) -> List[RemovedReservationDict]:
        country_code = cleaned_input["country_code"]
        variants = cleaned_input["products_variants"]

        reservations_total = get_user_reserved_quantity_bulk(
            info.context.user,
            country_code,
            variants,
        )

        remove_user_reservations(info.context.user, country_code, variants)

        removed_reservations = []
        for variant in variants:
            removed_reservations.append(
                {
                    "product_variant": variant,
                    "quantity": reservations_total[variant.id],
                }
            )

        return removed_reservations

    @classmethod
    def perform_mutation(cls, root, info, **data):
        cleaned_input = cls.clean_input(data["input"])
        removed_reservations = cls.delete(info, cleaned_input)
        return ReservationsRemove(removed_reservations=removed_reservations)

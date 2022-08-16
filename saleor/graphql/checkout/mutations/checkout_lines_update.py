from typing import Dict, List

import graphene
from django.forms import ValidationError

from ....checkout.error_codes import CheckoutErrorCode
from ....warehouse.reservations import is_reservation_enabled
from ...app.dataloaders import load_app
from ...checkout.types import CheckoutLine
from ...core.descriptions import (
    ADDED_IN_31,
    ADDED_IN_34,
    ADDED_IN_36,
    DEPRECATED_IN_3X_INPUT,
    PREVIEW_FEATURE,
)
from ...core.scalars import UUID, PositiveDecimal
from ...core.types import CheckoutError, NonNullList
from ...core.validators import validate_one_of_args_is_in_mutation
from ...product.types import ProductVariant
from ..types import Checkout
from .checkout_lines_add import CheckoutLinesAdd
from .utils import (
    check_lines_quantity,
    get_variants_and_total_quantities,
    group_lines_input_data_on_update,
)


class CheckoutLineUpdateInput(graphene.InputObjectType):
    variant_id = graphene.ID(
        required=False,
        description=(
            f"ID of the product variant. {DEPRECATED_IN_3X_INPUT} Use `lineId` instead."
        ),
    )
    quantity = graphene.Int(
        required=False,
        description=(
            "The number of items purchased. "
            "Optional for apps, required for any other users."
        ),
    )
    price = PositiveDecimal(
        required=False,
        description=(
            "Custom price of the item. Can be set only by apps "
            "with `HANDLE_CHECKOUTS` permission. When the line with the same variant "
            "will be provided multiple times, the last price will be used."
            + ADDED_IN_31
            + PREVIEW_FEATURE
        ),
    )
    line_id = graphene.ID(
        description="ID of the line." + ADDED_IN_36,
        required=False,
    )


class CheckoutLinesUpdate(CheckoutLinesAdd):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        id = graphene.ID(
            description="The checkout's ID." + ADDED_IN_34,
            required=False,
        )
        token = UUID(
            description=f"Checkout token.{DEPRECATED_IN_3X_INPUT} Use `id` instead.",
            required=False,
        )
        checkout_id = graphene.ID(
            required=False,
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} Use `id` instead."
            ),
        )
        lines = NonNullList(
            CheckoutLineUpdateInput,
            required=True,
            description=(
                "A list of checkout lines, each containing information about "
                "an item in the checkout."
            ),
        )

    class Meta:
        description = "Updates checkout line in the existing checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def validate_checkout_lines(
        cls,
        info,
        variants,
        checkout_lines_data,
        country,
        channel_slug,
        delivery_method_info,
        lines=None,
    ):
        variants, quantities = get_variants_and_total_quantities(
            variants, checkout_lines_data, quantity_to_update_check=True
        )

        check_lines_quantity(
            variants,
            quantities,
            country,
            channel_slug,
            info.context.site.settings.limit_quantity_per_checkout,
            delivery_method_info=delivery_method_info,
            allow_zero_quantity=True,
            existing_lines=lines,
            replace=True,
            check_reservations=is_reservation_enabled(info.context.site.settings),
        )

    @classmethod
    def clean_input(
        cls,
        info,
        checkout,
        variants,
        checkout_lines_data,
        checkout_info,
        lines,
        manager,
        discounts,
        replace,
    ):
        app = load_app(info.context)
        # if the requestor is not app, the quantity is required for all lines
        if not app:
            if any(
                [
                    line_data.quantity_to_update is False
                    for line_data in checkout_lines_data
                ]
            ):
                raise ValidationError(
                    {
                        "quantity": ValidationError(
                            "The quantity is required for all lines.",
                            code=CheckoutErrorCode.REQUIRED.value,
                        )
                    }
                )

        return super().clean_input(
            info,
            checkout,
            variants,
            checkout_lines_data,
            checkout_info,
            lines,
            manager,
            discounts,
            replace,
        )

    @classmethod
    def perform_mutation(
        cls, root, info, lines, checkout_id=None, token=None, id=None, replace=True
    ):
        for line in lines:
            validate_one_of_args_is_in_mutation(
                CheckoutErrorCode,
                "line_id",
                line.get("line_id"),
                "variant_id",
                line.get("variant_id"),
            )

        return super().perform_mutation(
            root, info, lines, checkout_id, token, id, replace=True
        )

    @classmethod
    def _get_variants_from_lines_input(cls, lines: List[Dict]) -> List[ProductVariant]:
        """Return list of ProductVariant objects.

        Uses variants ids or lines ids provided in CheckoutLineUpdateInput to
        fetch ProductVariant objects.
        """

        variant_ids = set()

        variant_ids.update(
            {line.get("variant_id") for line in lines if line.get("variant_id")}
        )

        line_ids = [line.get("line_id") for line in lines if line.get("line_id")]

        if line_ids:
            lines_instances = cls.get_nodes_or_error(line_ids, "line_id", CheckoutLine)
            variant_ids.update(
                {
                    graphene.Node.to_global_id("ProductVariant", line.variant_id)
                    for line in lines_instances
                }
            )

        return cls.get_nodes_or_error(variant_ids, "variant_id", ProductVariant)

    @classmethod
    def _get_grouped_lines_data(cls, lines, existing_lines_info):
        return group_lines_input_data_on_update(lines, existing_lines_info)

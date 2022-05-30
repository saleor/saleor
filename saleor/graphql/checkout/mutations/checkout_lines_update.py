import graphene
from django.forms import ValidationError

from ....checkout.error_codes import CheckoutErrorCode
from ....warehouse.reservations import is_reservation_enabled
from ...core.descriptions import ADDED_IN_34, DEPRECATED_IN_3X_INPUT
from ...core.scalars import UUID
from ...core.types import CheckoutError, NonNullList
from ..types import Checkout
from .checkout_create import CheckoutLineInput
from .checkout_lines_add import CheckoutLinesAdd
from .utils import check_lines_quantity


class CheckoutLineUpdateInput(CheckoutLineInput):
    quantity = graphene.Int(
        required=False,
        description=(
            "The number of items purchased. "
            "Optional for apps, required for any other users."
        ),
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
        lines=None,
    ):
        variants_to_validate = []
        quantities = []
        for variant, line_data in zip(variants, checkout_lines_data):
            if line_data.quantity_to_update:
                variants_to_validate.append(variant)
                quantities.append(line_data.quantity)

        check_lines_quantity(
            variants_to_validate,
            quantities,
            country,
            channel_slug,
            info.context.site.settings.limit_quantity_per_checkout,
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
        # if the requestor is not app, the quantity is required for all lines
        if not info.context.app:
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
    def perform_mutation(cls, root, info, lines, checkout_id=None, token=None, id=None):
        return super().perform_mutation(
            root, info, lines, checkout_id, token, id, replace=True
        )

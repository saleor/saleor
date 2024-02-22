import graphene
from django.forms import ValidationError

from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import CheckoutLineInfo
from ....warehouse.reservations import is_reservation_enabled
from ....webhook.event_types import WebhookEventAsyncType
from ...app.dataloaders import get_app_promise
from ...checkout.types import CheckoutLine
from ...core import ResolveInfo
from ...core.descriptions import (
    ADDED_IN_31,
    ADDED_IN_34,
    ADDED_IN_36,
    DEPRECATED_IN_3X_INPUT,
)
from ...core.doc_category import DOC_CATEGORY_CHECKOUT
from ...core.scalars import UUID, PositiveDecimal
from ...core.types import BaseInputObjectType, CheckoutError, NonNullList
from ...core.utils import WebhookEventInfo
from ...core.validators import validate_one_of_args_is_in_mutation
from ...product.types import ProductVariant
from ...site.dataloaders import get_site_promise
from ..types import Checkout
from .checkout_lines_add import CheckoutLinesAdd
from .utils import (
    CheckoutLineData,
    check_lines_quantity,
    get_variants_and_total_quantities,
    group_lines_input_data_on_update,
)


class CheckoutLineUpdateInput(BaseInputObjectType):
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
        ),
    )
    line_id = graphene.ID(
        description="ID of the line." + ADDED_IN_36,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_CHECKOUT


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
        doc_category = DOC_CATEGORY_CHECKOUT
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CHECKOUT_UPDATED,
                description="A checkout was updated.",
            )
        ]

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
        site = get_site_promise(info.context).get()
        check_lines_quantity(
            variants,
            quantities,
            country,
            channel_slug,
            site.settings.limit_quantity_per_checkout,
            delivery_method_info=delivery_method_info,
            allow_zero_quantity=True,
            existing_lines=lines,
            replace=True,
            check_reservations=is_reservation_enabled(site.settings),
        )

    @classmethod
    def clean_input(
        cls,
        info,
        checkout,
        variants,
        checkout_lines_data,
        checkout_info,
        lines_info,
        manager,
        replace,
    ):
        app = get_app_promise(info.context).get()
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

        cls._validate_gift_line(checkout_lines_data, lines_info)
        return super().clean_input(
            info,
            checkout,
            variants,
            checkout_lines_data,
            checkout_info,
            lines_info,
            manager,
            replace,
        )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, root, info: ResolveInfo, /, *, lines, checkout_id=None, token=None, id=None
    ):
        for line in lines:
            validate_one_of_args_is_in_mutation(
                "line_id",
                line.get("line_id"),
                "variant_id",
                line.get("variant_id"),
            )

        return super().perform_mutation(
            root,
            info,
            lines=lines,
            checkout_id=checkout_id,
            token=token,
            id=id,
            replace=True,
        )

    @classmethod
    def _get_variants_from_lines_input(cls, lines: list[dict]) -> list[ProductVariant]:
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

    @classmethod
    def _validate_gift_line(
        cls, lines_input: list[CheckoutLineData], lines_info: list[CheckoutLineInfo]
    ):
        existing_gift_ids = [
            str(line_info.line.id) for line_info in lines_info if line_info.line.is_gift
        ]
        if gift_lines_to_update := [
            line for line in lines_input if line.line_id in existing_gift_ids
        ]:
            global_ids = [
                graphene.Node.to_global_id("CheckoutLine", line.line_id)
                for line in gift_lines_to_update
            ]
            raise ValidationError(
                {
                    "line_id": ValidationError(
                        "Lines marked as gift can't be edited.",
                        code=CheckoutErrorCode.NON_EDITABLE_GIFT_LINE.value,
                        params={"lines": global_ids},
                    )
                }
            )

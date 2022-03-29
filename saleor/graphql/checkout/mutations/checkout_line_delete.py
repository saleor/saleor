import graphene

from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.utils import recalculate_checkout_discount
from ...core.descriptions import DEPRECATED_IN_3X_INPUT
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError
from ...core.validators import validate_one_of_args_is_in_mutation
from ..types import Checkout, CheckoutLine
from .utils import get_checkout_by_token, update_checkout_shipping_method_if_invalid


class CheckoutLineDelete(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} Use token instead."
            ),
            required=False,
        )
        token = UUID(description="Checkout token.", required=False)
        line_id = graphene.ID(description="ID of the checkout line to delete.")

    class Meta:
        description = "Deletes a CheckoutLine."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(cls, _root, info, line_id, checkout_id=None, token=None):
        # DEPRECATED
        validate_one_of_args_is_in_mutation(
            CheckoutErrorCode, "checkout_id", checkout_id, "token", token
        )

        if token:
            checkout = get_checkout_by_token(token)
        # DEPRECATED
        else:
            checkout = cls.get_node_or_error(
                info, checkout_id or token, only_type=Checkout, field="checkout_id"
            )

        line = cls.get_node_or_error(
            info, line_id, only_type=CheckoutLine, field="line_id"
        )

        if line and line in checkout.lines.all():
            line.delete()

        manager = info.context.plugins
        lines, _ = fetch_checkout_lines(checkout)
        checkout_info = fetch_checkout_info(
            checkout, lines, info.context.discounts, manager
        )
        update_checkout_shipping_method_if_invalid(checkout_info, lines)
        recalculate_checkout_discount(
            manager, checkout_info, lines, info.context.discounts
        )
        manager.checkout_updated(checkout)
        return CheckoutLineDelete(checkout=checkout)

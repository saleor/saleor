import graphene

from ....warehouse.reservations import is_reservation_enabled
from ...core.types.common import CheckoutError
from ..types import Checkout
from .checkout_lines_add import CheckoutLinesAdd
from .utils import check_lines_quantity


class CheckoutLinesUpdate(CheckoutLinesAdd):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Meta:
        description = "Updates checkout line in the existing checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def validate_checkout_lines(
        cls,
        info,
        variants,
        quantities,
        country,
        channel_slug,
        lines=None,
    ):
        check_lines_quantity(
            variants,
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
    def perform_mutation(cls, root, info, lines, checkout_id=None, token=None):
        return super().perform_mutation(
            root, info, lines, checkout_id, token, replace=True
        )

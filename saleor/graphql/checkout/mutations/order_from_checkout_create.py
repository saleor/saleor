import graphene
from django.core.exceptions import ValidationError

from ....checkout.checkout_cleaner import validate_checkout
from ....checkout.complete_checkout import create_order_from_checkout
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....core import analytics
from ....core.exceptions import GiftCardNotApplicable, InsufficientStock
from ....core.permissions import CheckoutPermissions
from ....discount.models import NotApplicable
from ...core.descriptions import PREVIEW_FEATURE
from ...core.mutations import BaseMutation
from ...core.types import Error
from ...order.types import Order
from ..enums import OrderFromCheckoutCreateErrorCode
from ..types import Checkout
from ..utils import prepare_insufficient_stock_checkout_validation_error


class OrderFromCheckoutCreateError(Error):
    code = OrderFromCheckoutCreateErrorCode(
        description="The error code.", required=True
    )
    variants = graphene.List(
        graphene.NonNull(graphene.ID),
        description="List of variant IDs which causes the error.",
        required=False,
    )
    lines = graphene.List(
        graphene.NonNull(graphene.ID),
        description="List of line Ids which cause the error.",
        required=False,
    )


class OrderFromCheckoutCreate(BaseMutation):
    order = graphene.Field(Order, description="Placed order.")

    class Arguments:
        id = graphene.ID(
            required=True,
            description="ID of a checkout that will be converted to an order.",
        )
        remove_checkout = graphene.Boolean(
            description=(
                "Determines if checkout should be removed after creating an order. "
                "Default true."
            ),
            default_value=True,
        )

    class Meta:
        description = f"{PREVIEW_FEATURE} Create new order from existing checkout."
        object_type = Order

        # FIXME this should be a separate permission probably
        permissions = (CheckoutPermissions.MANAGE_CHECKOUTS,)
        error_type_class = OrderFromCheckoutCreateError

    @classmethod
    def perform_mutation(cls, root, info, **data):
        checkout_id = data.get("id")
        checkout = cls.get_node_or_error(
            info, checkout_id, field="id", only_type=Checkout
        )
        tracking_code = analytics.get_client_id(info.context)
        # FIXME Do we want to limit this mutation only to App's token?

        discounts = info.context.discounts
        manager = info.context.plugins
        checkout_lines, unavailable_variant_pks = fetch_checkout_lines(checkout)
        checkout_info = fetch_checkout_info(
            checkout, checkout_lines, discounts, manager
        )

        validate_checkout(
            checkout_info=checkout_info,
            lines=checkout_lines,
            unavailable_variant_pks=unavailable_variant_pks,
            discounts=discounts,
            manager=manager,
        )

        try:
            order = create_order_from_checkout(
                checkout_info=checkout_info,
                checkout_lines=checkout_lines,
                discounts=info.context.discounts,
                manager=info.context.plugins,
                user=info.context.user,
                app=info.context.app,
                tracking_code=tracking_code,
                delete_checkout=data["remove_checkout"],
            )
        except NotApplicable:
            code = OrderFromCheckoutCreateErrorCode.VOUCHER_NOT_APPLICABLE.value
            raise ValidationError(
                {
                    "voucher_code": ValidationError(
                        "Voucher not applicable",
                        code=code,
                    )
                }
            )
        except InsufficientStock as e:
            error = prepare_insufficient_stock_checkout_validation_error(e)
            raise error
        except GiftCardNotApplicable as e:
            raise ValidationError({"gift_cards": e})

        return OrderFromCheckoutCreate(order=order)

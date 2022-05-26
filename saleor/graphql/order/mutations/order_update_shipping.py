import graphene
from django.core.exceptions import ValidationError

from ....core.permissions import OrderPermissions
from ....core.taxes import zero_taxed_money
from ....order import models
from ....order.actions import order_shipping_updated
from ....order.error_codes import OrderErrorCode
from ....order.utils import recalculate_order, update_order_prices
from ....shipping import models as shipping_models
from ....shipping.utils import convert_to_shipping_method_data
from ...core.mutations import BaseMutation
from ...core.types import OrderError
from ...shipping.types import ShippingMethod
from ..types import Order
from .utils import EditableOrderValidationMixin, clean_order_update_shipping


class OrderUpdateShippingInput(graphene.InputObjectType):
    shipping_method = graphene.ID(
        description="ID of the selected shipping method,"
        " pass null to remove currently assigned shipping method.",
        name="shippingMethod",
    )


class OrderUpdateShipping(EditableOrderValidationMixin, BaseMutation):
    order = graphene.Field(Order, description="Order with updated shipping method.")

    class Arguments:
        id = graphene.ID(
            required=True,
            name="order",
            description="ID of the order to update a shipping method.",
        )
        input = OrderUpdateShippingInput(
            description="Fields required to change shipping method of the order.",
            required=True,
        )

    class Meta:
        description = (
            "Updates a shipping method of the order."
            " Requires shipping method ID to update, when null is passed "
            "then currently assigned shipping method is removed."
        )
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        order = cls.get_node_or_error(
            info,
            data.get("id"),
            only_type=Order,
            qs=models.Order.objects.prefetch_related(
                "lines", "channel__shipping_method_listings"
            ),
        )
        cls.validate_order(order)

        data = data.get("input")

        if "shipping_method" not in data:
            raise ValidationError(
                {
                    "shipping_method": ValidationError(
                        "Shipping method must be provided to perform mutation.",
                        code=OrderErrorCode.SHIPPING_METHOD_REQUIRED,
                    )
                }
            )

        if not data.get("shipping_method"):
            if not order.is_draft() and order.is_shipping_required():
                raise ValidationError(
                    {
                        "shipping_method": ValidationError(
                            "Shipping method is required for this order.",
                            code=OrderErrorCode.SHIPPING_METHOD_REQUIRED,
                        )
                    }
                )

            # Shipping method is detached only when null is passed in input.
            if data["shipping_method"] == "":
                raise ValidationError(
                    {
                        "shipping_method": ValidationError(
                            "Shipping method cannot be empty.",
                            code=OrderErrorCode.SHIPPING_METHOD_REQUIRED,
                        )
                    }
                )

            order.shipping_method = None
            order.shipping_price = zero_taxed_money(order.currency)
            order.shipping_method_name = None
            order.save(
                update_fields=[
                    "currency",
                    "shipping_method",
                    "shipping_price_net_amount",
                    "shipping_price_gross_amount",
                    "shipping_method_name",
                    "updated_at",
                ]
            )
            recalculate_order(order)
            return OrderUpdateShipping(order=order)

        method = cls.get_node_or_error(
            info,
            data["shipping_method"],
            field="shipping_method",
            only_type=ShippingMethod,
            qs=shipping_models.ShippingMethod.objects.prefetch_related(
                "postal_code_rules"
            ),
        )
        shipping_channel_listing = (
            shipping_models.ShippingMethodChannelListing.objects.filter(
                shipping_method=method, channel=order.channel
            ).first()
        )
        if not shipping_channel_listing:
            raise ValidationError(
                {
                    "shipping_method": ValidationError(
                        "Shipping method not available in the given channel.",
                        code=OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.value,
                    )
                }
            )

        shipping_method_data = convert_to_shipping_method_data(
            method,
            shipping_channel_listing,
        )
        clean_order_update_shipping(order, shipping_method_data, info.context.plugins)

        order.shipping_method = method
        shipping_price = info.context.plugins.calculate_order_shipping(order)
        order.shipping_price = shipping_price
        order.shipping_tax_rate = info.context.plugins.get_order_shipping_tax_rate(
            order, shipping_price
        )
        order.shipping_method_name = method.name
        order.save(
            update_fields=[
                "currency",
                "shipping_method",
                "shipping_method_name",
                "shipping_price_net_amount",
                "shipping_price_gross_amount",
                "shipping_tax_rate",
                "updated_at",
            ]
        )
        update_order_prices(
            order,
            info.context.plugins,
            info.context.site.settings.include_taxes_in_prices,
        )
        # Post-process the results
        order_shipping_updated(order, info.context.plugins)
        return OrderUpdateShipping(order=order)

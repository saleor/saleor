import graphene
from django.core.exceptions import ValidationError

from ....core.permissions import OrderPermissions
from ....core.taxes import zero_money, zero_taxed_money
from ....order import models
from ....order.error_codes import OrderErrorCode
from ....order.utils import invalidate_order_prices
from ....shipping import models as shipping_models
from ....shipping.utils import convert_to_shipping_method_data
from ...core import ResolveInfo
from ...core.mutations import BaseMutation
from ...core.types import OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
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
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str, input
    ):
        order = cls.get_node_or_error(
            info,
            id,
            only_type=Order,
            qs=models.Order.objects.prefetch_related(
                "lines", "channel__shipping_method_listings"
            ),
        )
        cls.validate_order(order)

        if "shipping_method" not in input:
            raise ValidationError(
                {
                    "shipping_method": ValidationError(
                        "Shipping method must be provided to perform mutation.",
                        code=OrderErrorCode.SHIPPING_METHOD_REQUIRED.value,
                    )
                }
            )

        if not input.get("shipping_method"):
            if not order.is_draft() and order.is_shipping_required():
                raise ValidationError(
                    {
                        "shipping_method": ValidationError(
                            "Shipping method is required for this order.",
                            code=OrderErrorCode.SHIPPING_METHOD_REQUIRED.value,
                        )
                    }
                )

            # Shipping method is detached only when null is passed in input.
            if input["shipping_method"] == "":
                raise ValidationError(
                    {
                        "shipping_method": ValidationError(
                            "Shipping method cannot be empty.",
                            code=OrderErrorCode.SHIPPING_METHOD_REQUIRED.value,
                        )
                    }
                )

            order.shipping_method = None
            order.base_shipping_price = zero_money(order.currency)
            order.shipping_price = zero_taxed_money(order.currency)
            order.shipping_method_name = None
            order.shipping_tax_class = None
            order.shipping_tax_class_name = None
            order.shipping_tax_class_private_metadata = {}
            order.shipping_tax_class_metadata = {}
            invalidate_order_prices(order)
            order.save(
                update_fields=[
                    "currency",
                    "shipping_method",
                    "shipping_price_net_amount",
                    "shipping_price_gross_amount",
                    "base_shipping_price_amount",
                    "shipping_method_name",
                    "shipping_tax_class",
                    "shipping_tax_class_name",
                    "shipping_tax_class_private_metadata",
                    "shipping_tax_class_metadata",
                    "shipping_tax_rate",
                    "should_refresh_prices",
                    "updated_at",
                ]
            )
            return OrderUpdateShipping(order=order)

        method_id: str = input["shipping_method"]
        method: shipping_models.ShippingMethod = cls.get_node_or_error(
            info,
            method_id,
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
        manager = get_plugin_manager_promise(info.context).get()
        clean_order_update_shipping(order, shipping_method_data, manager)

        order.shipping_method = method
        order.shipping_method_name = method.name

        tax_class = method.tax_class
        if tax_class:
            order.shipping_tax_class = tax_class
            order.shipping_tax_class_name = tax_class.name
            order.shipping_tax_class_private_metadata = tax_class.private_metadata
            order.shipping_tax_class_metadata = tax_class.metadata

        order.base_shipping_price = shipping_method_data.price
        invalidate_order_prices(order)
        order.save(
            update_fields=[
                "currency",
                "shipping_method",
                "shipping_method_name",
                "shipping_tax_class",
                "shipping_tax_class_name",
                "shipping_tax_class_private_metadata",
                "shipping_tax_class_metadata",
                "base_shipping_price_amount",
                "should_refresh_prices",
                "updated_at",
            ]
        )
        # Post-process the results
        cls.call_event(manager.order_updated, order)
        return OrderUpdateShipping(order=order)

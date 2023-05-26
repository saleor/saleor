import graphene
from django.core.exceptions import ValidationError

from ....core.permissions import OrderPermissions
from ....order import models
from ....order.error_codes import OrderErrorCode
from ....shipping import models as shipping_models
from ....shipping.utils import convert_to_shipping_method_data
from ...core.mutations import BaseMutation
from ...core.types import OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
from ...shipping.types import ShippingMethod
from ..types import Order
from .utils import (
    SHIPPING_METHOD_UPDATE_FIELDS,
    EditableOrderValidationMixin,
    ShippingMethodUpdateMixin,
    clean_order_update_shipping,
)


class OrderUpdateShippingInput(graphene.InputObjectType):
    shipping_method = graphene.ID(
        description="ID of the selected shipping method,"
        " pass null to remove currently assigned shipping method.",
        name="shippingMethod",
    )


class OrderUpdateShipping(
    EditableOrderValidationMixin, ShippingMethodUpdateMixin, BaseMutation
):
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

            cls.clear_shipping_method_from_order(order)
            order.save(update_fields=SHIPPING_METHOD_UPDATE_FIELDS)
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
        shipping_channel_listing = cls.validate_shipping_channel_listing(method, order)

        shipping_method_data = convert_to_shipping_method_data(
            method,
            shipping_channel_listing,
        )
        manager = get_plugin_manager_promise(info.context).get()
        clean_order_update_shipping(order, shipping_method_data, manager)
        cls.update_shipping_method(order, method, shipping_channel_listing)

        order.save(update_fields=SHIPPING_METHOD_UPDATE_FIELDS)
        # Post-process the results
        cls.call_event(manager.order_updated, order)
        return OrderUpdateShipping(order=order)

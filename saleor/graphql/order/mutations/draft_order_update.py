import graphene
from django.core.exceptions import ValidationError

from ....core.permissions import OrderPermissions
from ....order import OrderStatus, models
from ....order.error_codes import OrderErrorCode
from ...app.dataloaders import load_app
from ...core.types import OrderError
from ...plugins.dataloaders import load_plugin_manager
from ..types import Order
from .draft_order_create import DraftOrderCreate, DraftOrderInput


class DraftOrderUpdate(DraftOrderCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a draft order to update.")
        input = DraftOrderInput(
            required=True, description="Fields required to update an order."
        )

    class Meta:
        description = "Updates a draft order."
        model = models.Order
        object_type = Order
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def get_instance(cls, info, **data):
        instance = super().get_instance(
            info, qs=models.Order.objects.prefetch_related("lines"), **data
        )
        if instance.status != OrderStatus.DRAFT:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Provided order id belongs to non-draft order. "
                        "Use `orderUpdate` mutation instead.",
                        code=OrderErrorCode.INVALID,
                    )
                }
            )
        return instance

    @classmethod
    def should_invalidate_prices(cls, instance, cleaned_input, is_new_instance) -> bool:
        return any(
            cleaned_input.get(field) is not None
            for field in [
                "shipping_address",
                "billing_address",
                "shipping_method",
            ]
        )

    @classmethod
    def save(cls, info, instance, cleaned_input):
        manager = load_plugin_manager(info.context)
        app = load_app(info.context)
        return cls._save_draft_order(
            info,
            instance,
            cleaned_input,
            is_new_instance=False,
            app=app,
            manager=manager,
        )

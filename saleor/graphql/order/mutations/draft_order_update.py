import graphene
from django.core.exceptions import ValidationError

from ....order import OrderStatus, models
from ....order.error_codes import OrderErrorCode
from ....permission.enums import OrderPermissions
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_310
from ...core.mutations import ModelWithExtRefMutation
from ...core.types import OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Order
from .draft_order_create import DraftOrderCreate, DraftOrderInput


class DraftOrderUpdate(DraftOrderCreate, ModelWithExtRefMutation):
    class Arguments:
        id = graphene.ID(required=False, description="ID of a draft order to update.")
        external_reference = graphene.String(
            required=False,
            description=f"External ID of a draft order to update. {ADDED_IN_310}",
        )
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
    def get_instance(cls, info: ResolveInfo, **data):
        instance = super().get_instance(
            info, qs=models.Order.objects.prefetch_related("lines"), **data
        )
        if instance.status != OrderStatus.DRAFT:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Provided order id belongs to non-draft order. "
                        "Use `orderUpdate` mutation instead.",
                        code=OrderErrorCode.INVALID.value,
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
    def save(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        app = get_app_promise(info.context).get()
        return cls._save_draft_order(
            info,
            instance,
            cleaned_input,
            is_new_instance=False,
            app=app,
            manager=manager,
        )

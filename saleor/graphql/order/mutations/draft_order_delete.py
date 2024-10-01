import graphene
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError

from ....core.tracing import traced_atomic_transaction
from ....discount.models import VoucherCode
from ....discount.utils.voucher import release_voucher_code_usage
from ....order import OrderStatus, models
from ....order.actions import call_order_event
from ....order.error_codes import OrderErrorCode
from ....permission.enums import OrderPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.mutations import (
    ModelDeleteWithRestrictedChannelAccessMutation,
    ModelWithExtRefMutation,
)
from ...core.types import OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Order


class DraftOrderDelete(
    ModelDeleteWithRestrictedChannelAccessMutation, ModelWithExtRefMutation
):
    class Arguments:
        id = graphene.ID(required=False, description="ID of a product to delete.")
        external_reference = graphene.String(
            required=False,
            description="External ID of a product to delete.",
        )

    class Meta:
        description = "Deletes a draft order."
        model = models.Order
        object_type = Order
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def clean_instance(cls, info: ResolveInfo, instance):
        if instance.status != OrderStatus.DRAFT:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Provided order id belongs to non-draft order.",
                        code=OrderErrorCode.INVALID.value,
                    )
                }
            )

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        order = cls.get_instance(info, **data)
        manager = get_plugin_manager_promise(info.context).get()
        try:
            with traced_atomic_transaction():
                response = super().perform_mutation(_root, info, **data)
                call_order_event(
                    manager,
                    WebhookEventAsyncType.DRAFT_ORDER_DELETED,
                    order,
                )
        except ProtectedError as e:
            items = ", ".join(
                [
                    item._meta.object_name
                    for item in e.protected_objects
                    if item._meta.object_name
                ]
            )
            raise ValidationError(
                ValidationError(
                    f"Draft order has attached items: {items}.",
                    code=OrderErrorCode.CANNOT_DELETE.value,
                )
            )
        return response

    @classmethod
    def get_instance_channel_id(cls, instance):
        return instance.channel_id

    @classmethod
    def post_save_action(cls, info, instance, _):
        if code := instance.voucher_code:
            if voucher_code := VoucherCode.objects.filter(code=code).first():
                voucher = voucher_code.voucher
                release_voucher_code_usage(voucher_code, voucher, None)

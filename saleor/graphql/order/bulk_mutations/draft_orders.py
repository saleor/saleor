import graphene
from django.core.exceptions import ValidationError

from ....core.permissions import OrderPermissions
from ....order import OrderStatus, models
from ....order.error_codes import OrderErrorCode
from ...core.mutations import ModelBulkDeleteMutation
from ...core.types import NonNullList, OrderError
from ..types import Order, OrderLine


class DraftOrderBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of draft order IDs to delete."
        )

    class Meta:
        description = "Deletes draft orders."
        model = models.Order
        object_type = Order
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def clean_instance(cls, info, instance):
        if instance.status != OrderStatus.DRAFT:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Cannot delete non-draft orders.",
                        code=OrderErrorCode.CANNOT_DELETE,
                    )
                }
            )


class DraftOrderLinesBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of order lines IDs to delete."
        )

    class Meta:
        description = "Deletes order lines."
        model = models.OrderLine
        object_type = OrderLine
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def clean_instance(cls, _info, instance):
        if instance.order.status != OrderStatus.DRAFT:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Cannot delete line for non-draft orders.",
                        code=OrderErrorCode.CANNOT_DELETE,
                    )
                }
            )

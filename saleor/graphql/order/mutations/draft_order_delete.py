import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ....core.permissions import OrderPermissions
from ....core.tracing import traced_atomic_transaction
from ....order import OrderStatus, models
from ....order.error_codes import OrderErrorCode
from ...core.mutations import ModelDeleteMutation
from ...core.types import OrderError
from ...plugins.dataloaders import load_plugin_manager
from ..types import Order


class DraftOrderDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a draft order to delete.")

    class Meta:
        description = "Deletes a draft order."
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
                        "Provided order id belongs to non-draft order.",
                        code=OrderErrorCode.INVALID,
                    )
                }
            )

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        order = cls.get_instance(info, **data)
        response = super().perform_mutation(_root, info, **data)
        manager = load_plugin_manager(info.context)
        transaction.on_commit(lambda: manager.draft_order_deleted(order))
        return response

from collections.abc import Iterable
from typing import Union
from uuid import UUID

import graphene
from django.core.exceptions import ValidationError

from ....channel import models as channel_models
from ....order import OrderStatus, models
from ....order.error_codes import OrderErrorCode
from ....payment.models import Payment, TransactionItem
from ....permission.enums import OrderPermissions
from ...core import ResolveInfo
from ...core.mutations import (
    BaseBulkWithRestrictedChannelAccessMutation,
    ModelBulkDeleteMutation,
)
from ...core.types import NonNullList, OrderError
from ..types import Order, OrderLine


class DraftOrderBulkDelete(
    ModelBulkDeleteMutation, BaseBulkWithRestrictedChannelAccessMutation
):
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
    def get_ids_with_related_objects(cls, ids, /):
        related_objects = {
            Payment.__name__: Payment.objects.values_list("order_id", flat=True)
            .filter(order_id__in=ids)
            .order_by()
            .distinct(),
            TransactionItem.__name__: TransactionItem.objects.values_list(
                "order_id", flat=True
            )
            .filter(order_id__in=ids)
            .order_by()
            .distinct(),
        }
        return related_objects

    @classmethod
    def clean_instance(cls, _info: ResolveInfo, instance, related_objects=None):
        if instance.status != OrderStatus.DRAFT:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Cannot delete non-draft orders.",
                        code=OrderErrorCode.CANNOT_DELETE.value,
                    )
                }
            )
        if related_objects and (
            instance.pk in related_objects[Payment.__name__]
            or instance.pk in related_objects[TransactionItem.__name__]
        ):
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Cannot delete orders with payments or transactions attached to it.",
                        code=OrderErrorCode.INVALID.value,
                    )
                }
            )

    @classmethod
    def get_channel_ids(cls, instances) -> Iterable[Union[UUID, int]]:
        """Get the instances channel ids for channel permission accessible check."""
        return [order.channel_id for order in instances]


class DraftOrderLinesBulkDelete(
    ModelBulkDeleteMutation, BaseBulkWithRestrictedChannelAccessMutation
):
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
    def clean_instance(cls, _info: ResolveInfo, instance, _related_objects=None):
        if instance.order.status != OrderStatus.DRAFT:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Cannot delete line for non-draft orders.",
                        code=OrderErrorCode.CANNOT_DELETE.value,
                    )
                }
            )

    @classmethod
    def get_channel_ids(cls, instances) -> Iterable[Union[UUID, int]]:
        """Get the instances channel ids for channel permission accessible check."""
        orders = models.Order.objects.filter(
            id__in=[line.order_id for line in instances]
        )
        return channel_models.Channel.objects.filter(
            id__in=orders.values("channel_id")
        ).values_list("id", flat=True)

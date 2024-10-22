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
                        "Cannot delete order with payments or transactions attached to it.",
                        code=OrderErrorCode.INVALID.value,
                    )
                }
            )

    @classmethod
    def clean_input(cls, info: ResolveInfo, instances, ids):
        clean_instance_ids = []
        errors_dict: dict[str, list[ValidationError]] = {}

        instances_ids = [instance.id for instance in instances]
        related_objects = cls.get_ids_with_related_objects(instances_ids)
        for instance, node_id in zip(instances, ids):
            instance_errors = []

            # catch individual validation errors to raise them later as
            # a single error
            try:
                cls.clean_instance(info, instance, related_objects)
            except ValidationError as e:
                msg = ". ".join(e.messages)
                instance_errors.append(msg)

            if not instance_errors:
                clean_instance_ids.append(instance.pk)
            else:
                instance_errors_msg = ". ".join(instance_errors)
                # FIXME we are not propagating code error from the raised ValidationError
                ValidationError({node_id: instance_errors_msg}).update_error_dict(
                    errors_dict
                )
        return clean_instance_ids, errors_dict

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
    def clean_instance(cls, _info: ResolveInfo, instance):
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

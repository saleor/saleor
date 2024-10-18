from collections.abc import Iterable
from typing import Optional, Union
from uuid import UUID

import graphene
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError

from ....channel import models as channel_models
from ....order import OrderStatus, models
from ....order.error_codes import OrderErrorCode
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
    def clean_instance(cls, _info: ResolveInfo, instance):
        if instance.status != OrderStatus.DRAFT:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Cannot delete non-draft orders.",
                        code=OrderErrorCode.CANNOT_DELETE.value,
                    )
                }
            )

    @classmethod
    def get_channel_ids(cls, instances) -> Iterable[Union[UUID, int]]:
        """Get the instances channel ids for channel permission accessible check."""
        return [order.channel_id for order in instances]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, ids, **data
    ) -> tuple[int, Optional[ValidationError]]:
        # code relies on the fact that both protected Models have FK named as `order`
        count, errors = 0, None
        try:
            count, errors = super().perform_mutation(_root, info, ids=ids, **data)
        except ProtectedError as e:
            error_dict: dict[str, list[ValidationError]] = {}
            for protected in e.protected_objects:
                if hasattr(protected, "order_id"):
                    node_id = graphene.Node.to_global_id("Order", protected.order_id)
                    error_message = f"Draft orders has attached items: {protected._meta.object_name}."
                    ValidationError(
                        {
                            node_id: ValidationError(
                                error_message, code=OrderErrorCode.CANNOT_DELETE.value
                            )
                        }
                    ).update_error_dict(error_dict)
            errors = ValidationError(error_dict)
        return count, errors


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

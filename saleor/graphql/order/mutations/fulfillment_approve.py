from typing import cast

import graphene
from django.core.exceptions import ValidationError

from ....account.models import User
from ....core.exceptions import InsufficientStock
from ....order import FulfillmentStatus
from ....order.actions import approve_fulfillment
from ....order.error_codes import OrderErrorCode
from ....permission.enums import OrderPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_31
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.types import OrderError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ...site.dataloaders import get_site_promise
from ..types import Fulfillment, Order
from ..utils import prepare_insufficient_stock_order_validation_errors
from .order_fulfill import OrderFulfill


class FulfillmentApprove(BaseMutation):
    fulfillment = graphene.Field(Fulfillment, description="An approved fulfillment.")
    order = graphene.Field(Order, description="Order which fulfillment was approved.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of a fulfillment to approve.")
        notify_customer = graphene.Boolean(
            required=True, description="True if confirmation email should be send."
        )
        allow_stock_to_be_exceeded = graphene.Boolean(
            default_value=False, description="True if stock could be exceeded."
        )

    class Meta:
        description = "Approve existing fulfillment." + ADDED_IN_31
        doc_category = DOC_CATEGORY_ORDERS
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.FULFILLMENT_APPROVED,
                description="Fulfillment is approved.",
            ),
        ]

    @classmethod
    def clean_input(cls, info: ResolveInfo, fulfillment):
        if fulfillment.status != FulfillmentStatus.WAITING_FOR_APPROVAL:
            raise ValidationError(
                "Invalid fulfillment status, only WAITING_FOR_APPROVAL "
                "fulfillments can be accepted.",
                code=OrderErrorCode.INVALID.value,
            )

        OrderFulfill.check_lines_for_preorder([line.order_line for line in fulfillment])
        site = get_site_promise(info.context).get()
        if (
            not site.settings.fulfillment_allow_unpaid
            and not fulfillment.order.is_fully_paid()
        ):
            raise ValidationError(
                "Cannot fulfill unpaid order.",
                code=OrderErrorCode.CANNOT_FULFILL_UNPAID_ORDER.value,
            )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        allow_stock_to_be_exceeded,
        id: str,
        notify_customer,
    ):
        user = info.context.user
        user = cast(User, user)
        fulfillment = cls.get_node_or_error(info, id, only_type=Fulfillment)
        order = fulfillment.order
        cls.check_channel_permissions(info, [order.channel_id])
        cls.clean_input(info, fulfillment)

        manager = get_plugin_manager_promise(info.context).get()
        app = get_app_promise(info.context).get()
        site = get_site_promise(info.context).get()
        try:
            fulfillment = approve_fulfillment(
                fulfillment,
                user,
                app,
                manager,
                site.settings,
                notify_customer=notify_customer,
                allow_stock_to_be_exceeded=allow_stock_to_be_exceeded,
            )
        except InsufficientStock as exc:
            errors = prepare_insufficient_stock_order_validation_errors(exc)
            raise ValidationError({"stocks": errors})

        order.refresh_from_db(fields=["status"])
        return FulfillmentApprove(fulfillment=fulfillment, order=order)

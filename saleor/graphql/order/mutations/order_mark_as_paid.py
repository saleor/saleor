from typing import TYPE_CHECKING, Optional, cast

import graphene
from django.core.exceptions import ValidationError

from ....account.models import User
from ....channel import MarkAsPaidStrategy
from ....order import models as order_models
from ....order.actions import (
    clean_mark_order_as_paid,
    mark_order_as_paid_with_payment,
    mark_order_as_paid_with_transaction,
)
from ....order.calculations import fetch_order_prices_if_expired
from ....order.error_codes import OrderErrorCode
from ....order.events import transaction_mark_order_as_paid_failed_event
from ....order.search import update_order_search_vector
from ....payment import PaymentError
from ....permission.enums import OrderPermissions
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.types import OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Order
from .utils import try_payment_action

if TYPE_CHECKING:
    from ....app.models import App
    from ....plugins.manager import PluginsManager


class OrderMarkAsPaid(BaseMutation):
    order = graphene.Field(Order, description="Order marked as paid.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the order to mark paid.")
        transaction_reference = graphene.String(
            required=False, description="The external transaction reference."
        )

    class Meta:
        description = "Mark order as manually paid."
        doc_category = DOC_CATEGORY_ORDERS
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def clean_billing_address(cls, instance):
        if not instance.billing_address:
            raise ValidationError(
                "Order billing address is required to mark order as paid.",
                code=OrderErrorCode.BILLING_ADDRESS_NOT_SET.value,
            )

    @classmethod
    def handle_mark_as_paid_for_payment(
        cls,
        order: "order_models.Order",
        request_user: User,
        app: Optional["App"],
        manager: "PluginsManager",
        external_reference: Optional[str] = None,
    ):
        try_payment_action(
            order, request_user, app, None, clean_mark_order_as_paid, order
        )
        mark_order_as_paid_with_payment(
            order=order,
            request_user=request_user,
            app=app,
            manager=manager,
            external_reference=external_reference,
        )

    @classmethod
    def handle_mark_as_paid_for_transaction(
        cls,
        order: "order_models.Order",
        request_user: User,
        app: Optional["App"],
        manager: "PluginsManager",
        external_reference: Optional[str] = None,
    ):
        try:
            clean_mark_order_as_paid(order=order)
        except (PaymentError, ValueError) as e:
            message = str(e)
            transaction_mark_order_as_paid_failed_event(
                order=order, user=request_user, app=app, message=message
            )
            raise ValidationError(
                {
                    "transaction": ValidationError(
                        message, code=OrderErrorCode.TRANSACTION_ERROR.value
                    )
                }
            )
        mark_order_as_paid_with_transaction(
            order=order,
            request_user=request_user,
            app=app,
            manager=manager,
            external_reference=external_reference,
        )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, transaction_reference=None
    ):
        order = cls.get_node_or_error(info, id, only_type=Order)
        cls.check_channel_permissions(info, [order.channel_id])
        manager = get_plugin_manager_promise(info.context).get()
        order, _ = fetch_order_prices_if_expired(order, manager)
        cls.clean_billing_address(order)
        user = info.context.user
        user = cast(User, user)
        app = get_app_promise(info.context).get()
        channel = order.channel
        if channel.order_mark_as_paid_strategy == MarkAsPaidStrategy.PAYMENT_FLOW:
            cls.handle_mark_as_paid_for_payment(
                order, user, app, manager, transaction_reference
            )
        else:
            cls.handle_mark_as_paid_for_transaction(
                order, user, app, manager, transaction_reference
            )

        update_order_search_vector(order)

        return OrderMarkAsPaid(order=order)

from typing import cast

import graphene
from django.core.exceptions import ValidationError

from ....account.models import User
from ....order.actions import clean_mark_order_as_paid, mark_order_as_paid
from ....order.calculations import fetch_order_prices_if_expired
from ....order.error_codes import OrderErrorCode
from ....order.search import update_order_search_vector
from ....permission.enums import OrderPermissions
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.mutations import BaseMutation
from ...core.types import OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Order
from .utils import try_payment_action


class OrderMarkAsPaid(BaseMutation):
    order = graphene.Field(Order, description="Order marked as paid.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the order to mark paid.")
        transaction_reference = graphene.String(
            required=False, description="The external transaction reference."
        )

    class Meta:
        description = "Mark order as manually paid."
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
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, transaction_reference=None
    ):
        order = cls.get_node_or_error(info, id, only_type=Order)
        manager = get_plugin_manager_promise(info.context).get()
        order, _ = fetch_order_prices_if_expired(order, manager)
        cls.clean_billing_address(order)
        user = info.context.user
        user = cast(User, user)
        app = get_app_promise(info.context).get()
        try_payment_action(order, user, app, None, clean_mark_order_as_paid, order)

        mark_order_as_paid(order, user, app, manager, transaction_reference)

        update_order_search_vector(order)

        return OrderMarkAsPaid(order=order)

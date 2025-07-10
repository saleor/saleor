from decimal import Decimal
from typing import TYPE_CHECKING, cast
from uuid import UUID

from django.core.exceptions import ValidationError
from django.core.validators import validate_ipv46_address

from .....account.models import User
from .....app.models import App
from .....checkout.actions import (
    transaction_amounts_for_checkout_updated_without_price_recalculation,
)
from .....core.exceptions import PermissionDenied
from .....core.tracing import traced_atomic_transaction
from .....core.utils import get_client_ip
from .....order import OrderStatus
from .....order import models as order_models
from .....order.actions import order_transaction_updated
from .....order.fetch import fetch_order_info
from .....order.search import update_order_search_vector
from .....order.utils import (
    calculate_order_granted_refund_status,
    refresh_order_status,
    updates_amounts_for_order,
)
from .....payment import models as payment_models
from .....payment.error_codes import TransactionUpdateErrorCode
from .....payment.lock_objects import (
    get_checkout_and_transaction_item_locked_for_update,
    get_order_and_transaction_item_locked_for_update,
)
from .....permission.enums import PaymentPermissions
from ....app.dataloaders import get_app_promise
from ....core.utils import from_global_id_or_error
from ...types import TransactionItem

if TYPE_CHECKING:
    from .....plugins.manager import PluginsManager


def get_transaction_item(
    id, token, error_field_name="id", qs=None
) -> payment_models.TransactionItem:
    """Get transaction based on token or global ID.

    The transactions created before 3.13 were using the `id` field as a graphql ID.
    From 3.13, the `token` is used as a graphql ID. All transactionItems created
    before 3.13 will use an `int` id as an identification.
    """
    if token:
        db_id = str(token)
    else:
        _, db_id = from_global_id_or_error(
            global_id=id, only_type=TransactionItem, raise_error=True
        )
    if db_id.isdigit():
        query_params = {"id": db_id, "use_old_id": True}
    else:
        query_params = {"token": db_id}
    if qs is None:
        qs = payment_models.TransactionItem.objects

    instance = qs.filter(**query_params).first()
    if not instance:
        raise ValidationError(
            {
                error_field_name: ValidationError(
                    f"Couldn't resolve to a node: {id}",
                    code=TransactionUpdateErrorCode.NOT_FOUND.value,
                )
            }
        )
    return instance


def clean_customer_ip_address(info, customer_ip_address: str | None, error_code: str):
    """Get customer IP address.

    The customer IP address is required for some payment gateways. By default, the
    customer IP address is taken from the request.

    If customer IP address is provided, we require the app to have the
    `PaymentPermissions.HANDLE_PAYMENTS` permission.
    """

    if not customer_ip_address:
        return get_client_ip(info.context)
    app = get_app_promise(info.context).get()
    if not app or not app.has_perm(PaymentPermissions.HANDLE_PAYMENTS):
        raise PermissionDenied(permissions=[PaymentPermissions.HANDLE_PAYMENTS])
    try:
        validate_ipv46_address(customer_ip_address)
    except ValidationError as e:
        raise ValidationError(
            {
                "customer_ip_address": ValidationError(
                    message=e.message,
                    code=error_code,
                )
            }
        ) from e
    return customer_ip_address


def process_order_with_transaction(
    transaction: payment_models.TransactionItem,
    manager: "PluginsManager",
    user: User | None,
    app: App | None,
    previous_authorized_value: Decimal = Decimal(0),
    previous_charged_value: Decimal = Decimal(0),
    previous_refunded_value: Decimal = Decimal(0),
    related_granted_refund: order_models.OrderGrantedRefund | None = None,
):
    order = None
    # This is executed after we ensure that the transaction is not a checkout
    # transaction, so we can safely cast the order_id to UUID.
    order_id = cast(UUID, transaction.order_id)
    with traced_atomic_transaction():
        order, transaction = get_order_and_transaction_item_locked_for_update(
            order_id, transaction.pk
        )
        update_fields = []
        updates_amounts_for_order(order, save=False)
        update_fields.extend(
            [
                "total_charged_amount",
                "charge_status",
                "total_authorized_amount",
                "authorize_status",
            ]
        )
        if (
            order.channel.automatically_confirm_all_new_orders
            and order.status == OrderStatus.UNCONFIRMED
        ):
            status_updated = refresh_order_status(order)
            if status_updated:
                update_fields.append("status")
        if update_fields:
            update_fields.append("updated_at")
            order.save(update_fields=update_fields)

    update_order_search_vector(order)
    order_info = fetch_order_info(order)
    order_transaction_updated(
        order_info=order_info,
        transaction_item=transaction,
        manager=manager,
        user=user,
        app=app,
        previous_authorized_value=previous_authorized_value,
        previous_charged_value=previous_charged_value,
        previous_refunded_value=previous_refunded_value,
    )
    if related_granted_refund:
        calculate_order_granted_refund_status(related_granted_refund)


def process_order_or_checkout_with_transaction(
    transaction: payment_models.TransactionItem,
    manager: "PluginsManager",
    user: User | None,
    app: App | None,
    previous_authorized_value: Decimal = Decimal(0),
    previous_charged_value: Decimal = Decimal(0),
    previous_refunded_value: Decimal = Decimal(0),
    related_granted_refund: order_models.OrderGrantedRefund | None = None,
):
    checkout_deleted = False
    if transaction.checkout_id:
        with traced_atomic_transaction():
            locked_checkout, transaction = (
                get_checkout_and_transaction_item_locked_for_update(
                    transaction.checkout_id, transaction.pk
                )
            )
            if transaction.checkout_id and locked_checkout:
                transaction_amounts_for_checkout_updated_without_price_recalculation(
                    transaction, locked_checkout, manager, user, app
                )
            else:
                checkout_deleted = True
                # If the checkout was deleted, we still want to update the order associated with the transaction.

    if transaction.order_id or checkout_deleted:
        process_order_with_transaction(
            transaction,
            manager,
            user,
            app,
            previous_authorized_value,
            previous_charged_value,
            previous_refunded_value,
            related_granted_refund=related_granted_refund,
        )

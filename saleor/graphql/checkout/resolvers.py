from ...checkout import models
from ...core.exceptions import PermissionDenied
from ...permission.enums import (
    AccountPermissions,
    CheckoutPermissions,
    PaymentPermissions,
)
from ..core.context import get_database_connection_name
from ..core.tracing import traced_resolver
from ..core.utils import from_global_id_or_error
from ..core.validators import validate_one_of_args_is_in_query
from ..utils import get_user_or_app_from_context


def resolve_checkout_lines(info):
    queryset = models.CheckoutLine.objects.using(
        get_database_connection_name(info.context)
    ).all()
    return queryset


def resolve_checkouts(info, channel_slug):
    queryset = models.Checkout.objects.using(
        get_database_connection_name(info.context)
    ).all()
    if channel_slug:
        queryset = queryset.filter(channel__slug=channel_slug)
    return queryset


@traced_resolver
def resolve_checkout(info, token, id):
    validate_one_of_args_is_in_query("id", id, "token", token)

    if id:
        _, token = from_global_id_or_error(id, only_type="Checkout")
    checkout = (
        models.Checkout.objects.using(get_database_connection_name(info.context))
        .filter(token=token)
        .first()
    )
    if checkout is None:
        return None
    # always return checkout for active channel
    if checkout.channel.is_active:
        return checkout

    # resolve checkout for staff or app
    if requester := get_user_or_app_from_context(info.context):
        has_manage_checkout = requester.has_perm(CheckoutPermissions.MANAGE_CHECKOUTS)
        has_impersonate_user = requester.has_perm(AccountPermissions.IMPERSONATE_USER)
        has_handle_payments = requester.has_perm(PaymentPermissions.HANDLE_PAYMENTS)
        if has_manage_checkout or has_impersonate_user or has_handle_payments:
            return checkout

    raise PermissionDenied(
        permissions=[
            CheckoutPermissions.MANAGE_CHECKOUTS,
            AccountPermissions.IMPERSONATE_USER,
            PaymentPermissions.HANDLE_PAYMENTS,
        ]
    )

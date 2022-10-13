from ...checkout import models
from ...core.permissions import AccountPermissions, CheckoutPermissions
from ...core.tracing import traced_resolver
from ..core.utils import from_global_id_or_error
from ..core.validators import validate_one_of_args_is_in_query
from ..utils import get_user_or_app_from_context


def resolve_checkout_lines():
    queryset = models.CheckoutLine.objects.all()
    return queryset


def resolve_checkouts(channel_slug):
    queryset = models.Checkout.objects.all()
    if channel_slug:
        queryset = queryset.filter(channel__slug=channel_slug)
    return queryset


@traced_resolver
def resolve_checkout(info, token, id):
    validate_one_of_args_is_in_query("id", id, "token", token)

    if id:
        _, token = from_global_id_or_error(id, only_type="Checkout")
    checkout = models.Checkout.objects.filter(token=token).first()

    if checkout is None:
        return None

    # resolve checkout in active channel
    if checkout.channel.is_active:
        # resolve checkout for anonymous customer
        if not checkout.user:
            return checkout

        # resolve checkout for logged-in customer
        if checkout.user == info.context.user:
            return checkout

    # resolve checkout for staff user
    requester = get_user_or_app_from_context(info.context)

    has_manage_checkout = requester.has_perm(CheckoutPermissions.MANAGE_CHECKOUTS)
    has_impersonate_user = requester.has_perm(AccountPermissions.IMPERSONATE_USER)
    if has_manage_checkout or has_impersonate_user:
        return checkout

    return None

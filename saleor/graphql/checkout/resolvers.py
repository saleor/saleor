from ...checkout import models
from ...core.permissions import CheckoutPermissions
from ..utils import get_user_or_app_from_context


def resolve_checkout_lines():
    queryset = models.CheckoutLine.objects.all()
    return queryset


def resolve_checkouts():
    queryset = models.Checkout.objects.all()
    return queryset


def resolve_checkout(info, token):
    checkout = models.Checkout.objects.filter(token=token).first()

    if checkout is None:
        return None

    # resolve checkout for anonymous customer
    if not checkout.user:
        return checkout

    # resolve checkout for logged-in customer
    if checkout.user == info.context.user:
        return checkout

    # resolve checkout for staff user
    requester = get_user_or_app_from_context(info.context)
    if requester.has_perm(CheckoutPermissions.MANAGE_CHECKOUTS):
        return checkout

    return None

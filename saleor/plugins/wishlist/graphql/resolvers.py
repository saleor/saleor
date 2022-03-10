from typing import TYPE_CHECKING

from saleor.core.tracing import traced_resolver

from ..models import Wishlist

if TYPE_CHECKING:
    from graphene.types import ResolveInfo

    from saleor.account.models import User


def resolve_wishlist_from_user(user: "User") -> Wishlist:
    """Return wishlist of the logged-in user."""
    wishlist, _ = Wishlist.objects.get_or_create(user=user)
    return wishlist


@traced_resolver
def resolve_wishlist_from_info(info: "ResolveInfo") -> Wishlist:
    """Return wishlist of the logged-in user."""
    user = info.context.user
    return resolve_wishlist_from_user(user)


def resolve_wishlist_items_from_user(user: "User") -> "Wishlist":
    """Return wishlist items of the logged-in user."""
    return resolve_wishlist_from_user(user)

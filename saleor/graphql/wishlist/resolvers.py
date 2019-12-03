from typing import List

from graphene.types import ResolveInfo

from ...wishlist.models import Wishlist, WishlistItem
from ...wishlist.session_helpers import WishlistSessionHelper


def get_wishlist_from_info(info: ResolveInfo) -> Wishlist:
    """Return wishlist depending on the user.

    For anonymous users return wishlist stored in the session
    and for the logged in its private one.
    """
    user = info.context.user
    if user.is_anonymous:
        session = info.context.session
        wsh = WishlistSessionHelper(session)
        wishlist = wsh.get_or_create_wishlist()
    else:
        wishlist = Wishlist.objects.get_or_create_wishlist_for_user(user)
    return wishlist


def resolve_wishlist_items(info: ResolveInfo) -> List[WishlistItem]:
    """Return all the items of a wishlist obtained from the "info" object."""
    wishlist = get_wishlist_from_info(info)
    return wishlist.items.all()

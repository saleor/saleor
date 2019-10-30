from typing import List

from ...wishlist.models import Wishlist, WishlistItem
from ...wishlist.session_helpers import WishlistSessionHelper


def get_wishlist_from_info(info) -> Wishlist:
    user = info.context.user
    if user.is_anonymous:
        session = info.context.session
        wsh = WishlistSessionHelper(session)
        wishlist = wsh.get_or_create_wishlist()
    else:
        wishlist = Wishlist.objects.get_or_create_wishlist_for_user(user)
    return wishlist


def resolve_wishlist_items(info) -> List[WishlistItem]:
    wishlist = get_wishlist_from_info(info)
    return wishlist.items.all()

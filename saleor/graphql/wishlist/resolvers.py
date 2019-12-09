from typing import TYPE_CHECKING, List

from ...wishlist.models import Wishlist

if TYPE_CHECKING:
    # pylint: disable=unused-import
    from graphene.types import ResolveInfo
    from ...account.models import User


def resolve_wishlist_from_user(user: "User") -> Wishlist:
    """Return wishlist of the logged in user."""
    wishlist = Wishlist.objects.get_or_create(user)
    return wishlist


def resolve_wishlist_from_info(info: "ResolveInfo") -> Wishlist:
    """Return wishlist of the logged in user."""
    user = info.context.user
    return resolve_wishlist_from_user(user)


def resolve_wishlist_items_from_user(user: "User") -> List[Wishlist]:
    """Return wishlist items of the logged in user."""
    wishlist = resolve_wishlist_from_user(user)
    return wishlist.items.all()

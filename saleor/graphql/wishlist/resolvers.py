from typing import TYPE_CHECKING, List

from graphql_jwt.decorators import login_required

from ...wishlist.models import Wishlist, WishlistItem

if TYPE_CHECKING:
    # flake8: noqa
    from graphene.types import ResolveInfo
    from ...account.models import User


@login_required
def resolve_wishlist_from_info(info: "ResolveInfo") -> Wishlist:
    """Return wishlist of the logged in user."""
    user = info.context.user
    return Wishlist.objects.get_or_create_wishlist_for_user(user)


@login_required
def resolve_wishlist_items_from_info(info: "ResolveInfo") -> List[WishlistItem]:
    """Return wishlist of the logged in user."""
    user = info.context.user
    wishlist = Wishlist.objects.get_or_create_wishlist_for_user(user)
    return wishlist.items.all()

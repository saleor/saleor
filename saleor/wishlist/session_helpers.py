from django.contrib.auth.signals import user_logged_in

from .models import Wishlist, WishlistItem

SESSION_WISHLIST_TOKEN_NAME = "WISHLIST"


class WishlistSessionHelper:
    def __init__(self, session):
        self.session = session

    def _get_wishlist_token(self):
        return self.session.get(SESSION_WISHLIST_TOKEN_NAME, None)

    def _store_wishlist_token(self, token):
        self.session[SESSION_WISHLIST_TOKEN_NAME] = str(token)
        self.session.save()

    def get_wishlist(self):
        token = self._get_wishlist_token()
        if token:
            try:
                return Wishlist.objects.get(token=token)
            except Wishlist.DoesNotExist:
                return None
        return None

    def get_or_create_wishlist(self):
        wishlist = self.get_wishlist()
        if not wishlist:
            wishlist = Wishlist.objects.create()
            self._store_wishlist_token(wishlist.token)
        return wishlist

    def clear(self):
        del self.session[SESSION_WISHLIST_TOKEN_NAME]
        self.session.save()


def update_wishlist_on_user_login(sender, request, user, **kwargs):
    wsh = WishlistSessionHelper(request.session)
    wishlist = wsh.get_wishlist()
    if wishlist:
        if hasattr(user, "wishlist"):
            # User already has a wishlist, lets copy the WishlistItems from
            # the session's one to the user's one
            WishlistItem.objects.move_items_between_wishlists(wishlist, user.wishlist)
            wishlist.delete()
        else:
            wishlist.set_user(user)
        # Remove the Wishlist's token from the session
        wsh.clear()


user_logged_in.connect(update_wishlist_on_user_login)

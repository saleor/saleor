import pytest
from django.shortcuts import reverse

from saleor.wishlist.models import Wishlist, WishlistItem
from saleor.wishlist.session_helpers import WishlistSessionHelper


def test_update_wishlist_from_session_on_login_for_user_without_wishlist(
    client, customer_user, variant
):
    # Add Wishlist items to the session
    session = client.session
    wsh = WishlistSessionHelper(session)
    wishlist = wsh.get_or_create_wishlist()
    wishlist.add_variant(variant)
    # Assert that user doesn't have a Wishlist
    with pytest.raises(Wishlist.DoesNotExist):
        customer_user.wishlist
    # Login user which should create Wishlist from the session
    url = reverse("account:login")
    response = client.post(
        url,
        {"username": customer_user.email, "password": customer_user._password},
        follow=True,
    )
    assert response.status_code == 200
    # Check that everything was created correctly
    customer_user.refresh_from_db()
    assert customer_user.wishlist == wishlist


def test_update_wishlist_from_session_on_login_for_user_with_wishlist(
    client, customer_wishlist, variant
):
    customer_user = customer_wishlist.user
    # Add Wishlist items to the session
    session = client.session
    wsh = WishlistSessionHelper(session)
    wishlist = wsh.get_or_create_wishlist()
    wishlist.add_variant(variant)
    [wishlist_item] = wishlist.items.all()
    # Login user which should merge Wishlist from the session to the user's one
    url = reverse("account:login")
    response = client.post(
        url,
        {"username": customer_user.email, "password": customer_user._password},
        follow=True,
    )
    assert response.status_code == 200
    # Check that the original wishlist was preserved
    customer_user.refresh_from_db()
    assert customer_user.wishlist == customer_wishlist
    # Check it contains an item from the session's wishlist
    assert customer_wishlist.items.count() == 1
    wishlist_item.refresh_from_db()
    assert wishlist_item.wishlist == customer_wishlist
    # Check that the session's wishlist was deleted
    with pytest.raises(Wishlist.DoesNotExist):
        wishlist.refresh_from_db()


def test_remove_only_variant_also_removes_wishlist_item(customer_wishlist_item):
    assert customer_wishlist_item.variants.count() == 1
    variant = customer_wishlist_item.variants.first()
    wishlist = customer_wishlist_item.wishlist
    assert wishlist.items.count() == 1
    wishlist.remove_variant(variant)
    assert wishlist.items.count() == 0
    with pytest.raises(WishlistItem.DoesNotExist):
        customer_wishlist_item.refresh_from_db()


def test_remove_single_variant_from_wishlist_item(
    customer_wishlist_item_with_two_variants
):
    assert customer_wishlist_item_with_two_variants.variants.count() == 2
    [variant_1, variant_2] = customer_wishlist_item_with_two_variants.variants.all()
    wishlist = customer_wishlist_item_with_two_variants.wishlist
    wishlist.remove_variant(variant_1)
    customer_wishlist_item_with_two_variants.refresh_from_db()
    assert customer_wishlist_item_with_two_variants.variants.count() == 1
    assert customer_wishlist_item_with_two_variants.variants.first() == variant_2

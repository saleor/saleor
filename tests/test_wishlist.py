from __future__ import unicode_literals
import pytest

from saleor.product.models import AttributeChoiceValue, ProductVariant
from saleor.wishlist.models import Wishlist, WishlistItem, WishlistNotification
from saleor.wishlist import utils
from saleor.discount.models import Sale


@pytest.fixture()
def available_variant(product_in_stock, size_attribute):
    product= product_in_stock
    variant = product.variants.get(sku='123')
    attribute_value = AttributeChoiceValue.objects.filter(
        attribute=size_attribute)[0]
    variant.set_attribute(size_attribute.pk, attribute_value.pk)
    variant.save()
    return variant


@pytest.fixture()
def unavailable_variant(product_in_stock, size_attribute):
    product= product_in_stock
    attribute_value = AttributeChoiceValue.objects.filter(
        attribute=size_attribute)[1]
    variant = ProductVariant.objects.create(product=product, sku='124')
    variant.set_attribute(size_attribute.pk, attribute_value.pk)
    variant.save()
    return variant


@pytest.fixture()
def notify_product(product_in_stock, available_variant, unavailable_variant):
    return product_in_stock


@pytest.fixture()
def wishlist(customer_user):
    wishlist, created = Wishlist.objects.get_or_create(user=customer_user)
    return wishlist

@pytest.fixture()
def wishlist_item_available(wishlist, available_variant):
    return WishlistItem.objects.create(
        wishlist=wishlist,
        product=available_variant.product,
        attributes=available_variant.attributes,
        watch=True)


@pytest.fixture()
def wishlist_item_unavailable(wishlist, unavailable_variant):
    return WishlistItem.objects.create(
        wishlist=wishlist,
        product=unavailable_variant.product,
        attributes=unavailable_variant.attributes,
        watch=True)


@pytest.fixture()
def wishlist_item_missing_variant(wishlist, notify_product):
    return WishlistItem.objects.create(
        wishlist=wishlist,
        product=notify_product,
        attributes={'1': '42'},
        watch=True)


@pytest.fixture()
def wishlist_with_items(wishlist,
                        wishlist_item_available,
                        wishlist_item_unavailable,
                        wishlist_item_missing_variant):
    return wishlist


def test_variant_getter(wishlist_with_items,
                        wishlist_item_available,
                        wishlist_item_unavailable,
                        wishlist_item_missing_variant,
                        available_variant,
                        unavailable_variant):
    assert wishlist_item_missing_variant.variant is None
    assert wishlist_item_available.variant == available_variant
    assert wishlist_item_unavailable.variant == unavailable_variant


def test_get_wishlistitem_url(available_variant,
                              wishlist_item_available,
                              wishlist_item_missing_variant):
    variant_url = available_variant.get_absolute_url() + "?Size=big"
    assert utils.get_wishlistitem_url(wishlist_item_available) == variant_url
    product_url = available_variant.product.get_absolute_url()
    assert utils.get_wishlistitem_url(
        wishlist_item_missing_variant) == product_url


def test_add_to_user_wishlist(wishlist, customer_user, available_variant):
    assert not wishlist.wishlistitem_set.all().exists()
    utils.add_to_user_wishlist(customer_user, available_variant.product,
                               available_variant.attributes)
    assert wishlist.wishlistitem_set.all().exists()


def test_clear_notifications(wishlist, available_variant, unavailable_variant):
    WishlistNotification.objects.create(wishlist=wishlist,
                                        variant=available_variant)
    WishlistNotification.objects.create(wishlist=wishlist,
                                        variant=unavailable_variant)
    assert WishlistNotification.objects.all().exists()
    utils.clear_notifications()
    assert not WishlistItem.objects.all().exists()


def test_variant_available(available_variant, unavailable_variant):
    assert utils.variant_available(available_variant)
    assert not utils.variant_available(unavailable_variant)


def test_create_notifications(wishlist_with_items, wishlist_item_available,
                              available_variant, admin_user):
    utils.create_notifications(turn_off_watcher=False)
    assert WishlistNotification.objects.all().count() == 1
    assert WishlistNotification.objects.all().first(
    ).variant == available_variant
    wishlist_item_available.refresh_from_db()
    assert wishlist_item_available.watch
    utils.update_notifications()
    wishlist_item_available.refresh_from_db()
    assert not wishlist_item_available.watch


def test_get_wishlists_with_notifications(available_variant, wishlist,
                                          admin_user):
    Wishlist.objects.create(user=admin_user)
    assert Wishlist.objects.all().count() == 2
    WishlistNotification.objects.create(variant=available_variant,
                                        wishlist=wishlist)
    wishlists = utils.get_wishlists_with_notifications()
    assert wishlists.count() == 1
    assert wishlists.first() == wishlist


def test_add_variant_to_user_wishlist(available_variant, customer_user):
    is_added = utils.add_variant_to_user_wishlist(
    customer_user, available_variant)
    assert is_added
    is_added = utils.add_variant_to_user_wishlist(
    customer_user, available_variant)
    assert not is_added

def test_wishlist_item_info(wishlist_item_available, wishlist_item_missing_variant):
    info = utils.wishlist_item_info(wishlist_item_available)
    assert info.get('available')

def test_wishlist_items_with_availability(wishlist_item_unavailable, wishlist_item_available):
    discounts = Sale.objects.all()
    items = list(utils.wishlist_items_with_availability([wishlist_item_unavailable, wishlist_item_available], discounts))
    assert len(items) == 2
    # check availability for items
    assert not items[0][1].available
    assert items[1][1].available


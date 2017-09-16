import emailit
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.utils.encoding import smart_text

from ..core.utils import build_absolute_uri
from ..product.models import ProductVariant
from ..product.utils import (
    get_availability, get_variant_availability, get_variant_url)
from .models import Wishlist, WishlistItem, WishlistNotification


def get_wishlistitem_url(wishlist_item):
    # type: (WishlistItem) -> str
    """Returns url to product or variant, if available."""
    variant = wishlist_item.variant
    if variant:
        return get_variant_url(variant)
    return wishlist_item.product.get_absolute_url()


def add_variant_to_user_wishlist(user, variant):
    # type: (User, ProductVariant) -> bool
    """
    Adds variant to user wishlist.
    """
    wishlist, created = Wishlist.objects.get_or_create(user=user)
    # notify user if product was unavailable during adding to list
    watch = not variant.is_in_stock()
    item, created = WishlistItem.objects.get_or_create(
        wishlist=wishlist, product=variant.product,
        attributes=variant.attributes, variant_object=variant,
        defaults={'watch': watch})
    return created


def add_to_user_wishlist(user, product, attributes):
    # type: (User, Product, dict) -> bool
    """Adds item chosen by attributes to user product list. Will try to find
    variant with matching attributes."""
    if product.product_class.variant_attributes.exists():
        variant = ProductVariant.objects.filter(
            product=product, attributes=attributes).first()
        if variant:
            return add_variant_to_user_wishlist(user, variant)
    wishlist, _ = Wishlist.objects.get_or_create(user=user)
    item, created = WishlistItem.objects.get_or_create(
        wishlist=wishlist, product=product, attributes=attributes,
        defaults={'watch': True})
    return created


def clear_notifications():
    # type: () -> None
    """Removes all notification objects from db."""
    WishlistNotification.objects.all().delete()


def variant_available(variant):
    # type: (ProductVariant) -> bool
    """Test if variant should generate notification."""
    return all([variant.product.is_available(),
                variant.is_in_stock()])


def create_notifications(turn_off_watcher=True):
    # type: (bool) -> None
    """Create Wishlist notifications if variants are available.
    If notification is created, turn off watcher."""
    wli = WishlistItem.objects.all().filter(watch=True).order_by(
        'product', 'attributes').distinct('product', 'attributes')
    for wishlist_item in wli:
        product = wishlist_item.product
        attributes = wishlist_item.attributes
        variant = ProductVariant.objects.filter(product=product,
                                                attributes=attributes).first()
        if variant is None or not variant_available(variant):
            continue
        items_to_notify = WishlistItem.objects.all().filter(
            watch=True, product=product, attributes=attributes)
        for item in items_to_notify:
            WishlistNotification.objects.create(wishlist=item.wishlist,
                                                variant=variant)
        if turn_off_watcher:
            items_to_notify.update(watch=False)


def update_notifications():
    # type: () -> None
    """Remove all old Wishlist notifications and create new."""
    clear_notifications()
    create_notifications()


def get_wishlists_with_notifications():
    # type: () -> django.db.models.QuerySet
    queryset = Wishlist.objects.all()
    queryset = queryset.prefetch_related('wishlistnotification_set')
    queryset = queryset.annotate(
        notification_count=Count('wishlistnotification__id'))
    queryset = queryset.filter(notification_count__gt=0)
    return queryset


def get_users_and_notifications():
    # type: () -> typing.Iterator[tuple[User, list[ProductVariant]]]
    """
    Returns generator producing tuple in format (user, [list of variants])
    from notifications.
    """
    wishlists = get_wishlists_with_notifications()
    for wishlist in wishlists:
        user = wishlist.user
        items = wishlist.wishlistnotification_set.all()
        yield (user, [item.variant for item in items])


def send_notification_email(user, items):
    # type: (User, list) -> None
    """Send to user all its notifications."""
    url = build_absolute_uri(reverse('wishlist:user-wishlist'))
    emailit.api.send_mail(user.email,
                          {'items': items, 'url': url},
                          'wishlist/emails/notification',
                          from_email=settings.NOTIFICATION_FROM_EMAIL)


def update_and_send_wishlist_notifications():
    # type: () -> None
    """Update all notification data and send email to users."""
    update_notifications()
    for user, items in get_users_and_notifications():
        send_notification_email(user, items)


def wishlist_item_variant_name(item):
    # type: (WishlistItem) -> str
    """Get WishlistItem display name."""
    if item.variant:
        return item.variant.display_variant()
    attributes = item.product.product_class.variant_attributes.all()
    attribute_displays = []
    for attribute in attributes:
        values = {smart_text(v.pk): smart_text(v)
                  for v in attribute.values.all()}
        attribute_displays.append(
            '%s: %s' % (smart_text(attribute),
                        values[item.attributes[smart_text(attribute.pk)]]))
    return ', '.join(attribute_displays)


def wishlist_item_info(item):
    # type: (WishlistItem) -> dict
    """
    Get WishlistItem information about it's product and variant.
    """
    variant = item.variant
    product = item.product
    variant_name = wishlist_item_variant_name(item)
    image = product.get_first_image()
    available = False
    if variant is not None:
        available = variant_available(variant)

    return {
        'product': item.product,
        'variant': variant,
        'variant_name': variant_name,
        'available': available,
        'url': get_wishlistitem_url(item),
        'image': image,
        'delete_url': reverse('wishlist:item-delete',
                              kwargs={'item_pk': item.pk})}


def wishlist_items_with_availability(items, discounts, local_currency=None):
    # type: (list, list, Optional[str]) -> typing.Iterator[tuple]
    """Generate information about availability and prices of provided
    WishlistItem.
    """
    for item in items:
        item_info = wishlist_item_info(item)
        if item_info['variant'] is not None:
            availability = get_variant_availability(item_info['variant'],
                                                    discounts,
                                                    local_currency)
        else:
            availability = get_availability(item.product,
                                            discounts,
                                            local_currency)
        yield item_info, availability

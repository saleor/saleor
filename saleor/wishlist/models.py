import uuid

from django.db import models, transaction

from ..account.models import User
from ..product.models import Product, ProductVariant


class Wishlist(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.OneToOneField(
        User, related_name="wishlist", on_delete=models.CASCADE, blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def set_user(self, user):
        self.user = user
        self.save()

    def get_all_variants(self):
        return ProductVariant.objects.filter(
            wishlist_items__wishlist_id=self.pk
        ).distinct()

    def add_product(self, product: Product):
        item, _is_created = self.items.get_or_create(product_id=product.pk)
        return item

    def remove_product(self, product: Product):
        self.items.filter(product_id=product.pk).delete()

    def add_variant(self, variant: ProductVariant):
        item, _is_created = self.items.get_or_create(product_id=variant.product_id)
        item.variants.add(variant)
        return item

    def remove_variant(self, variant: ProductVariant):
        try:
            item = self.items.get(product_id=variant.product_id)
        except WishlistItem.DoesNotExist:
            return
        else:
            item.variants.remove(variant)
            # If it was the last variant, delete the whole item
            if item.variants.count() == 0:
                item.delete()


class WishlistItemQuerySet(models.QuerySet):
    @transaction.atomic()
    def move_items_between_wishlists(self, src_wishlist, dst_wishlist):
        dst_wishlist_map = {}
        for dst_item in dst_wishlist.items.all():
            dst_wishlist_map[dst_item.product_id] = dst_item
        # Copying the items from the source to the destination wishlist.
        for src_item in src_wishlist.items.all():
            if src_item.product_id in dst_wishlist_map:
                # This wishlist item's product already exist.
                # Adding and the variants, "add" already handles duplicates.
                dst_item = dst_wishlist_map[src_item.product_id]
                dst_item.variants.add(*src_item.variants.all())
                src_item.delete()
            else:
                # This wishlist item contains a new product.
                # It can be reassigned to the destination wishlist.
                src_item.wishlist = dst_wishlist
                src_item.save()
        self.filter(wishlist=src_wishlist).update(wishlist=dst_wishlist)


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(
        Wishlist, related_name="items", on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product, related_name="wishlist_items", on_delete=models.CASCADE
    )
    variants = models.ManyToManyField(
        ProductVariant, related_name="wishlist_items", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = WishlistItemQuerySet.as_manager()

    class Meta:
        unique_together = ("wishlist", "product")

    def __str__(self):
        return "WishlistItem (%s, %s)" % (self.wishlist.user, self.product)

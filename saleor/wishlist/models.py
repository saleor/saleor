from __future__ import unicode_literals

from uuid import uuid4

from django.contrib.postgres.fields import HStoreField
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible, smart_text

from ..core.utils import build_absolute_uri
from ..product.models import Product, ProductVariant
from ..userprofile.models import User


@python_2_unicode_compatible
class Wishlist(models.Model):
    user = models.ForeignKey(User)
    token = models.UUIDField(default=uuid4, editable=False, unique=True)
    public = models.BooleanField(default=False)

    def change_token(self, save=False):
        self.token = uuid4()
        if save:
            self.save(update_fields=['token'])

    def __str__(self):
        return 'Wishlist (%s)' % smart_text(self.user)

    def get_absolute_public_url(self):
        return build_absolute_uri(reverse('wishlist:public-wishlist',
                                          kwargs={'token': self.token}))


@python_2_unicode_compatible
class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist)
    product = models.ForeignKey(Product)
    variant_object = models.ForeignKey(ProductVariant, null=True)
    attributes = HStoreField(default={})
    watch = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('wishlist', 'product', 'variant_object',
                           'attributes')

    def __str__(self):
        if self.variant:
            return "%s - %s" % (smart_text(self.product),
                                smart_text(self.variant))
        else:
            return "%s" % smart_text(self.product)

    @property
    def variant(self):
        if self.variant_object:
            return self.variant_object
        for variant in self.product.variants.all():
            if variant.attributes == self.attributes:
                self.variant_object = variant
                self.save()
                return variant
        return None


@python_2_unicode_compatible
class WishlistNotification(models.Model):
    wishlist = models.ForeignKey(Wishlist)
    variant = models.ForeignKey(ProductVariant)

    class Meta:
        unique_together = ('wishlist', 'variant')

    def __str__(self):
        return "%s - %s" % (smart_text(self.product),
                            smart_text(self.variant))

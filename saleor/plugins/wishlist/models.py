import uuid

from django.db import models

from saleor.account.models import User
from saleor.product.models import Product, ProductVariant


class Wishlist(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, blank=True, null=True)
    products = models.ManyToManyField(Product)
    variants = models.ManyToManyField(ProductVariant)

    created_at = models.DateTimeField(auto_now_add=True)

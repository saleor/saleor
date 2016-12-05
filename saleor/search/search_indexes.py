from __future__ import unicode_literals

from haystack import indexes
from ..product.models import Product
from ..order.models import Order
from ..userprofile.models import User


class ProductIndex(indexes.SearchIndex, indexes.Indexable):
    name = indexes.CharField(model_attr='name')
    available_on = indexes.DateField(model_attr='available_on', null=True)
    text = indexes.MultiValueField(document=True)
    categories = indexes.MultiValueField()

    def get_model(self):
        return Product

    def index_queryset(self, using=None):
        qs = self.get_model().objects.all()
        qs = qs.prefetch_related('categories', 'images', 'variants')
        return qs

    def prepare_categories(self, obj):
        return list(obj.categories.values_list('name', flat=True))

    def prepare_text(self, obj):
        text_to_index = [obj.name, obj.description]
        for variant in obj.variants.all():
            text_to_index.append(variant.name)
            text_to_index.append(variant.sku)
        return text_to_index


class OrderIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.MultiValueField(document=True)

    def get_model(self):
        return Order

    def index_queryset(self, using=None):
        return self.get_model().objects.select_related(
            'billing_address', 'shipping_address', 'user')

    def prepare_text(self, obj):
        billing = obj.billing_address
        shipping = obj.shipping_address
        email = obj.user_email
        if not email and obj.user:
            email = obj.user.email
        return [email, billing.phone, shipping.phone]


class UserIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.MultiValueField(document=True)

    def get_model(self):
        return User

    def index_queryset(self, using=None):
        return self.get_model().objects.prefetch_related('addresses')

    def prepare_text(self, obj):
        data = [obj.email]
        for address in obj.addresses.all():
            data.append(address.first_name)
            data.append(address.last_name)
            data.append(address.phone)
        return data

from haystack import indexes
from ..product.models import ProductVariant, Product
from ..order.models import Order
from ..userprofile.models import User


class ProductVariantIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return ProductVariant

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


class ProductIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return Product

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


class OrderIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return Order

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


class UserIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return User

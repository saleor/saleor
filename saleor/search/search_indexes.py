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
        qs = qs.prefetch_related('categories')
        return qs

    def prepare_categories(self, obj):
        return list(obj.categories.values_list('name', flat=True))

    def prepare_text(self, obj):
        return [obj.name, obj.description]


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
        email_parts = email.split('@')
        return [email, billing.phone, shipping.phone] + email_parts


class UserIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.MultiValueField(document=True)

    def get_model(self):
        return User

    def prepare_text(self, obj):
        email_parts = obj.email.split('@')
        return [obj.email] + email_parts

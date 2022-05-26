from graphene_django import DjangoObjectType

from saleor.product.models import ProductVariant
from saleor.order.models import OrderLine

class CloneProductType(DjangoObjectType):
    class Meta:
        model = ProductVariant
        fields = "__all__"

class AlterOrderlineType(DjangoObjectType):
    class Meta:
        model = OrderLine
        fields = "__all__"

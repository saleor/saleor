import graphene
from ...core.types import FilterInputObjectType
from ..enums import OrderDirection, ProductOrderField
from ..filters import ProductFilter


class ProductOrder(graphene.InputObjectType):
    field = graphene.Argument(
        ProductOrderField, required=True,
        description='Sort products by the selected field.')
    direction = graphene.Argument(
        OrderDirection, required=True,
        description='Specifies the direction in which to sort products')


class ProductFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = ProductFilter

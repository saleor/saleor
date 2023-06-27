import graphene
from graphene import relay
from ...core import ResolveInfo
from ...core.scalars import PositiveDecimal
from ...discount.enums import DiscountValueTypeEnum
from ...core.types import ModelObjectType
from ...product.types import Category
from ...core.connection import CountableConnection
from ....b2b import models

class CategoryDiscount(ModelObjectType[models.CategoryDiscount]):
    id = graphene.GlobalID()
    category = graphene.Field(Category)
    value = PositiveDecimal()
    value_type = graphene.Field(DiscountValueTypeEnum)

    class Meta:
        description = "Represents category discount data"
        interfaces = [relay.Node]
        model = models.CategoryDiscount

    @staticmethod
    def resolve_category(root: models.CategoryDiscount, info:ResolveInfo):
        return root.category

class CategoryDiscountCountableConnection(CountableConnection):
    class Meta:
        node = CategoryDiscount
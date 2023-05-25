import graphene
from graphene import relay

from ....discount import models
from ....permission.enums import OrderPermissions
from ...core import ResolveInfo
from ...core.fields import PermissionsField
from ...core.scalars import PositiveDecimal
from ...core.types import ModelObjectType, Money
from ..enums import DiscountValueTypeEnum, OrderDiscountTypeEnum


class OrderDiscount(ModelObjectType[models.OrderDiscount]):
    id = graphene.GlobalID(required=True)
    type = OrderDiscountTypeEnum(required=True)
    name = graphene.String()
    translated_name = graphene.String()
    value_type = graphene.Field(
        DiscountValueTypeEnum,
        required=True,
        description="Type of the discount: fixed or percent",
    )
    value = PositiveDecimal(
        required=True,
        description="Value of the discount. Can store fixed value or percent value",
    )
    reason = PermissionsField(
        graphene.String,
        required=False,
        description="Explanation for the applied discount.",
        permissions=[
            OrderPermissions.MANAGE_ORDERS,
        ],
    )
    amount = graphene.Field(
        Money, description="Returns amount of discount.", required=True
    )

    class Meta:
        description = (
            "Contains all details related to the applied discount to the order."
        )
        interfaces = [relay.Node]
        model = models.OrderDiscount

    @staticmethod
    def resolve_reason(root: models.OrderDiscount, _info: ResolveInfo):
        return root.reason

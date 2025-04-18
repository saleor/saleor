from typing import TypeVar

import graphene
from django.db.models.base import Model
from graphene import relay

from ....core.prices import quantize_price
from ....discount import models
from ....permission.enums import OrderPermissions
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_321
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.fields import PermissionsField
from ...core.scalars import PositiveDecimal
from ...core.types import ModelObjectType, Money
from ...order.dataloaders import OrderLineByIdLoader
from ..enums import DiscountValueTypeEnum, OrderDiscountTypeEnum

N = TypeVar("N", bound=Model)


class BaseOrderDiscount(ModelObjectType[N]):
    id = graphene.GlobalID(required=True, description="The ID of discount applied.")
    type = OrderDiscountTypeEnum(
        required=True,
        description="The type of applied discount: Sale, Voucher or Manual.",
    )
    name = graphene.String(description="The name of applied discount.")
    translated_name = graphene.String(
        description="Translated name of the applied discount."
    )
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

    class Meta:
        abstract = True


class OrderDiscount(BaseOrderDiscount[models.OrderDiscount]):
    amount = graphene.Field(
        Money,
        description="Returns amount of discount.",
        required=True,
        deprecation_reason="Use `total` instead.",
    )

    total = graphene.Field(
        Money,
        required=True,
        description="The amount of discount applied to the order." + ADDED_IN_321,
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

    @staticmethod
    def resolve_total(root: models.OrderLineDiscount, info):
        return root.amount


class OrderLineDiscount(BaseOrderDiscount[models.OrderLineDiscount]):
    total = graphene.Field(
        Money,
        required=True,
        description="The discount amount applied to the line item.",
    )
    unit = graphene.Field(
        Money,
        required=True,
        description="The discount amount applied to the single line unit.",
    )

    class Meta:
        description = "Represent the discount applied to order line."
        doc_category = DOC_CATEGORY_ORDERS
        model = models.OrderLineDiscount

    @staticmethod
    def resolve_total(root: models.OrderLineDiscount, info):
        return root.amount

    @staticmethod
    def resolve_unit(root: models.OrderLineDiscount, info):
        def with_order_line(order_line):
            if not order_line:
                return root.amount
            return quantize_price(root.amount / order_line.quantity, root.currency)

        return (
            OrderLineByIdLoader(info.context).load(root.line_id).then(with_order_line)
        )

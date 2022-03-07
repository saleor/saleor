import graphene
from graphene import relay

from ....discount import models
from ....permission.enums import OrderPermissions
from ...meta.types import ObjectWithMetadata
from ...core import ResolveInfo
from ...core.fields import PermissionsField
from ...core.scalars import PositiveDecimal
from ...core.types import ModelObjectType, Money
from ..enums import DiscountValueTypeEnum, DiscountTypeEnum, DiscountTypeEnum


class BaseObjectDiscount(graphene.Interface):
    id = graphene.GlobalID(required=True)
    type = DiscountTypeEnum(required=True)
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
    amount = graphene.Field(
        Money, description="Returns amount of discount.", required=True
    )
    reason = graphene.String(
        required=False, description="Explanation for the applied discount."
    )
    active = graphene.Boolean(
        required=True, description="Determines if a discount active."
    )
    code = graphene.String(required=False, description="Code of applied discount.")


class OrderDiscount(ModelObjectType[models.OrderDiscount]):
    id = graphene.GlobalID(required=True, description="The ID of discount applied.")
    type = DiscountTypeEnum(
        required=True,
        description="The type of applied discount: Sale, Voucher or Manual.",
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
        description = (
            "Contains all details related to the applied discount to the order."
        )
        interfaces = [relay.Node, BaseObjectDiscount, ObjectWithMetadata]
        model = models.OrderDiscount

    @staticmethod
    def resolve_reason(root: models.OrderDiscount, _info: ResolveInfo):
        return root.reason


class OrderLineDiscount(ModelObjectType):
    class Meta:
        description = (
            "Contains all details related to the applied discount to the order line."
        )
        interfaces = [relay.Node, BaseObjectDiscount, ObjectWithMetadata]
        # TODO: Change to real model, in final PR.
        model = models.OrderDiscount
        # model = models.OrderLineDiscount


class OrderShippingDiscount(ModelObjectType):
    class Meta:
        description = (
            "Contains all details related to the applied discount to "
            "the order shipping."
        )
        interfaces = [relay.Node, BaseObjectDiscount, ObjectWithMetadata]
        # TODO: Change to real model, in final PR.
        model = models.OrderDiscount
        # model = models.OrderShippingDiscount


class CheckoutDiscount(ModelObjectType):
    class Meta:
        description = (
            "Contains all details related to the applied discount to the checkout."
        )
        interfaces = [relay.Node, BaseObjectDiscount, ObjectWithMetadata]
        # TODO: Change to real model, in final PR.
        model = models.OrderDiscount
        # model = models.CheckoutDiscount


class CheckoutLineDiscount(ModelObjectType):
    class Meta:
        description = (
            "Contains all details related to the applied discount to the checkout line."
        )
        interfaces = [relay.Node, BaseObjectDiscount, ObjectWithMetadata]
        # TODO: Change to real model, in final PR.
        model = models.OrderDiscount
        # model = models.CheckoutLineDiscount


class CheckoutShippingDiscount(ModelObjectType):
    class Meta:
        description = (
            "Contains all details related to the applied discount to "
            "the checkout shipping."
        )
        interfaces = [relay.Node, BaseObjectDiscount, ObjectWithMetadata]
        # TODO: Change to real model, in final PR.
        model = models.OrderDiscount
        # model = models.CheckoutShippingDiscount

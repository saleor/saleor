import graphene
from django.core.exceptions import ValidationError

from ....order import models
from ....permission.enums import OrderPermissions
from ...core.descriptions import ADDED_IN_313, PREVIEW_FEATURE
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import ModelMutation
from ...core.scalars import Decimal
from ...core.types import BaseInputObjectType
from ...core.types.common import Error
from ..enums import OrderGrantRefundUpdateErrorCode
from ..types import Order, OrderGrantedRefund


class OrderGrantRefundUpdateError(Error):
    code = OrderGrantRefundUpdateErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderGrantRefundUpdateInput(BaseInputObjectType):
    amount = Decimal(description="Amount of the granted refund.")
    reason = graphene.String(description="Reason of the granted refund.")

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderGrantRefundUpdate(ModelMutation):
    order = graphene.Field(
        Order, description="Order which has assigned updated grant refund."
    )
    granted_refund = graphene.Field(
        OrderGrantedRefund, description="Created granted refund."
    )

    class Arguments:
        id = graphene.ID(description="ID of the granted refund.", required=True)
        input = OrderGrantRefundUpdateInput(
            required=True,
            description="Fields required to update a granted refund.",
        )

    class Meta:
        description = "Updates granted refund." + ADDED_IN_313 + PREVIEW_FEATURE
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderGrantRefundUpdateError
        model = models.OrderGrantedRefund
        object_type = OrderGrantedRefund
        doc_category = DOC_CATEGORY_ORDERS

    @classmethod
    def validate_input(cls, amount, reason):
        if not amount and not reason:
            error_msg = (
                "At least amount or reason need to be provided to process update."
            )
            raise ValidationError(
                {
                    "input": ValidationError(
                        error_msg, code=OrderGrantRefundUpdateErrorCode.REQUIRED.value
                    )
                }
            )

    @classmethod
    def success_response(cls, instance):
        return cls(order=instance.order, granted_refund=instance)

    @classmethod
    def clean_input(cls, info, instance, data, input_cls=None):
        cleaned_input = super().clean_input(info, instance, data, input_cls=input_cls)
        amount = cleaned_input.pop("amount", None)
        cls.validate_input(amount, data.get("reason"))
        if amount is not None:
            cleaned_input["amount_value"] = amount
        return cleaned_input

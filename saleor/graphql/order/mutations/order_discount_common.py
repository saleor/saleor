import graphene
from django.core.exceptions import ValidationError
from prices import Money

from ....order import models
from ....order.error_codes import OrderErrorCode
from ...core import ResolveInfo
from ...core.mutations import BaseMutation
from ...core.scalars import PositiveDecimal
from ...discount.enums import DiscountValueTypeEnum


class OrderDiscountCommonInput(graphene.InputObjectType):
    value_type = graphene.Field(
        DiscountValueTypeEnum,
        required=True,
        description="Type of the discount: fixed or percent",
    )
    value = PositiveDecimal(
        required=True,
        description="Value of the discount. Can store fixed value or percent value",
    )
    reason = graphene.String(
        required=False, description="Explanation for the applied discount."
    )


class OrderDiscountCommon(BaseMutation):
    class Meta:
        abstract = True

    @classmethod
    def validate_order(cls, _info: ResolveInfo, order: models.Order) -> models.Order:
        if not (order.is_draft() or order.is_unconfirmed()):
            error_msg = "Only draft and unconfirmed order can be modified."
            raise ValidationError(
                {
                    "orderId": ValidationError(
                        error_msg, code=OrderErrorCode.CANNOT_DISCOUNT.value
                    )
                }
            )
        return order

    @classmethod
    def _validation_error_for_input_value(
        cls, error_msg, code=OrderErrorCode.INVALID.value
    ):
        return ValidationError({"value": ValidationError(error_msg, code=code)})

    @classmethod
    def validate_order_discount_input(cls, _info, max_total: Money, input: dict):
        value_type = input["value_type"]
        value = input["value"]
        if value_type == DiscountValueTypeEnum.FIXED:
            if value > max_total.amount:
                error_msg = (
                    f"The value ({value}) cannot be higher than {max_total.amount} "
                    f"{max_total.currency}"
                )
                raise cls._validation_error_for_input_value(error_msg)
        elif value > 100:
            error_msg = f"The percentage value ({value}) cannot be higher than 100."
            raise cls._validation_error_for_input_value(error_msg)

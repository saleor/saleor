import graphene
from django.core.exceptions import ValidationError

from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.models import Checkout
from ....checkout.utils import invalidate_checkout_prices
from ....core.permissions import CheckoutPermissions
from ....graphql.core.mutations import BaseMutation
from ....order import ORDER_EDITABLE_STATUS
from ....order.models import Order
from ....tax import error_codes
from ...core.descriptions import ADDED_IN_38, PREVIEW_FEATURE
from ...core.types import Error
from ...core.types.taxes import TaxSourceObject
from ...discount.dataloaders import load_discounts

TaxExemptionManageErrorCode = graphene.Enum.from_enum(
    error_codes.TaxExemptionManageErrorCode
)


class TaxExemptionManageError(Error):
    code = TaxExemptionManageErrorCode(description="The error code.", required=True)


class TaxExemptionManage(BaseMutation):
    taxable_object = graphene.Field(TaxSourceObject)

    class Arguments:
        id = graphene.ID(
            description="ID of the Checkout or Order object.", required=True
        )
        tax_exemption = graphene.Boolean(
            description="Determines if a taxes should be exempt.", required=True
        )

    class Meta:
        description = (
            "Exempt checkout or order from charging the taxes. When tax exemption is "
            "enabled, taxes won't be charged for the checkout or order. Taxes may "
            "still be calculated in cases when product prices are entered with the "
            "tax included and the net price needs to be known."
            + ADDED_IN_38
            + PREVIEW_FEATURE
        )
        error_type_class = TaxExemptionManageError
        permissions = (CheckoutPermissions.MANAGE_TAXES,)

    @classmethod
    def validate_input(cls, info, data):
        obj = cls.get_node_or_error(info, data["id"])
        if not isinstance(obj, (Order, Checkout)):
            code = error_codes.TaxExemptionManageErrorCode.NOT_FOUND.value
            message = "Invalid object ID. Only Checkout and Order ID's are accepted."
            raise ValidationError({"id": ValidationError(code=code, message=message)})

    @classmethod
    def validate_order_status(cls, order):
        if order.status not in ORDER_EDITABLE_STATUS:
            code = error_codes.TaxExemptionManageErrorCode.NOT_EDITABLE_ORDER.value
            message = (
                "Tax exemption can be manage only on orders in "
                f"{ORDER_EDITABLE_STATUS} statuses."
            )
            raise ValidationError(code=code, message=message)

    @classmethod
    def get_object(cls, info, object_global_id):
        obj = graphene.Node.get_node_from_global_id(info, object_global_id)
        return obj

    @classmethod
    def _invalidate_checkout_prices(cls, info, checkout):
        discounts = load_discounts(info.context)

        checkout_info = fetch_checkout_info(
            checkout, [], discounts, info.context.plugins
        )
        lines_info, _ = fetch_checkout_lines(checkout)
        invalidate_checkout_prices(
            checkout_info,
            lines_info,
            info.context.plugins,
            discounts,
            save=False,
        )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        cls.validate_input(info, data)
        obj = cls.get_object(info, data["id"])
        obj.tax_exemption = data["tax_exemption"]

        if isinstance(obj, Checkout):
            cls._invalidate_checkout_prices(info, obj)
            obj.save(update_fields=["tax_exemption", "price_expiration", "last_change"])

        if isinstance(obj, Order):
            cls.validate_order_status(obj)
            obj.should_refresh_prices = True
            obj.save(
                update_fields=["tax_exemption", "should_refresh_prices", "updated_at"]
            )

        return TaxExemptionManage(taxable_object=obj)

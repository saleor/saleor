import graphene
from django.core.exceptions import ValidationError

from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.models import Checkout as Checkout
from ....checkout.utils import invalidate_checkout_prices
from ....core.permissions import CheckoutPermissions
from ....graphql.checkout.types import Checkout as CheckoutType
from ....graphql.core.mutations import BaseMutation
from ....graphql.order.types import Order as OrderType
from ....order import ORDER_EDITABLE_STATUS
from ....order.models import Order as Order
from ....tax import error_codes
from ...core.types import Error

TaxExemptionManageErrorCode = graphene.Enum.from_enum(
    error_codes.TaxExemptionManageErrorCode
)


class TaxExemptionManageError(Error):
    code = TaxExemptionManageErrorCode(description="The error code.", required=True)


TAXABLE_OBJECTS_MAP = {Order: OrderType, Checkout: CheckoutType}


class TaxableObject(graphene.Union):
    class Meta:
        types = tuple(TAXABLE_OBJECTS_MAP.values())

    @classmethod
    def resolve_type(cls, instance, info):
        instance_type = type(instance)
        return TAXABLE_OBJECTS_MAP[instance_type]


class TaxExemptionManage(BaseMutation):
    taxable_object = graphene.Field(TaxableObject)

    class Arguments:
        id = graphene.ID(description="ID of the Checkout or Order object.")
        tax_exemption = graphene.Boolean()

    class Meta:
        description = "Exempt taxes for Checkout or Order."
        error_type_class = TaxExemptionManageError
        permissions = (CheckoutPermissions.MANAGE_TAXES,)

    @classmethod
    def validate_input(cls, data):
        obj_type, _ = graphene.Node.from_global_id(data["id"])

        if obj_type not in ["Order", "Checkout"]:
            code = error_codes.TaxExemptionManageErrorCode.INVALID_OBJECT_ID.value
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
        checkout_info = fetch_checkout_info(
            checkout, [], info.context.discounts, info.context.plugins
        )
        lines_info, _ = fetch_checkout_lines(checkout)
        invalidate_checkout_prices(
            checkout_info,
            lines_info,
            info.context.plugins,
            info.context.discounts,
            save=False,
        )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        cls.validate_input(data)
        obj = cls.get_object(info, data["id"])
        obj.tax_exemption = data["tax_exemption"]

        if isinstance(obj, Checkout):
            cls._invalidate_checkout_prices(info, obj)
            obj.save(update_fields=["tax_exemption", "price_expiration", "last_change"])

        if isinstance(obj, Order):
            cls.validate_order_status(obj)
            obj.should_refresh_prices = True
            obj.save(update_fields=["tax_exemption", "should_refresh_prices"])

        return TaxExemptionManage(taxable_object=obj)

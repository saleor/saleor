import graphene

from ...account import error_codes as account_error_codes
from ...checkout import error_codes as checkout_error_codes
from ...core import error_codes as shop_error_codes
from ...core.permissions import MODELS_PERMISSIONS
from ...core.weight import WeightUnits
from ...extensions import error_codes as extensions_error_codes
from ...extensions.plugins.vatlayer import TaxRateType as CoreTaxRateType
from ...giftcard import error_codes as giftcard_error_codes
from ...menu import error_codes as menu_error_codes
from ...order import error_codes as order_error_codes
from ...payment import error_codes as payment_error_codes
from ...product import error_codes as product_error_codes
from ...shipping import error_codes as shipping_error_codes
from ...webhook import error_codes as webhook_error_codes
from .utils import str_to_enum

# FIXME CoreTaxRateType should be removed after we will drop old api fields dedicated
#  to taxes


class ReportingPeriod(graphene.Enum):
    TODAY = "TODAY"
    THIS_MONTH = "THIS_MONTH"


def to_enum(enum_cls, *, type_name=None, **options) -> graphene.Enum:
    """Create a Graphene enum from a class containing a set of options.

    :param enum_cls:
        The class to build the enum from.
    :param type_name:
        The name of the type. Default is the class name + 'Enum'.
    :param options:
        - description:
            Contains the type description (default is the class's docstring)
        - deprecation_reason:
            Contains the deprecation reason.
            The default is enum_cls.__deprecation_reason__ or None.
    :return:
    """

    # note this won't work until
    # https://github.com/graphql-python/graphene/issues/956 is fixed
    deprecation_reason = getattr(enum_cls, "__deprecation_reason__", None)
    if deprecation_reason:
        options.setdefault("deprecation_reason", deprecation_reason)

    type_name = type_name or (enum_cls.__name__ + "Enum")
    enum_data = [(str_to_enum(code.upper()), code) for code, name in enum_cls.CHOICES]
    return graphene.Enum(type_name, enum_data, **options)


TaxRateType = graphene.Enum(
    "TaxRateType", [(str_to_enum(rate[0]), rate[0]) for rate in CoreTaxRateType.CHOICES]
)


PermissionEnum = graphene.Enum(
    "PermissionEnum",
    [
        (str_to_enum(codename.split(".")[1]), codename)
        for codename in MODELS_PERMISSIONS
    ],
)


WeightUnitsEnum = graphene.Enum(
    "WeightUnitsEnum", [(str_to_enum(unit[0]), unit[0]) for unit in WeightUnits.CHOICES]
)


AccountErrorCode = graphene.Enum.from_enum(account_error_codes.AccountErrorCode)
CheckoutErrorCode = graphene.Enum.from_enum(checkout_error_codes.CheckoutErrorCode)
ExtensionsErrorCode = graphene.Enum.from_enum(
    extensions_error_codes.ExtensionsErrorCode
)
GiftCardErrorCode = graphene.Enum.from_enum(giftcard_error_codes.GiftCardErrorCode)
MenuErrorCode = graphene.Enum.from_enum(menu_error_codes.MenuErrorCode)
OrderErrorCode = graphene.Enum.from_enum(order_error_codes.OrderErrorCode)
PaymentErrorCode = graphene.Enum.from_enum(payment_error_codes.PaymentErrorCode)
ProductErrorCode = graphene.Enum.from_enum(product_error_codes.ProductErrorCode)
ShopErrorCode = graphene.Enum.from_enum(shop_error_codes.ShopErrorCode)
ShippingErrorCode = graphene.Enum.from_enum(shipping_error_codes.ShippingErrorCode)
WebhookErrorCode = graphene.Enum.from_enum(webhook_error_codes.WebhookErrorCode)

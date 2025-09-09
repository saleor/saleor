import graphene
from django.conf import settings

from ...account import error_codes as account_error_codes
from ...app import error_codes as app_error_codes
from ...attribute import error_codes as attribute_error_codes
from ...channel import error_codes as channel_error_codes
from ...checkout import error_codes as checkout_error_codes
from ...core import JobStatus, TimePeriodType
from ...core import error_codes as core_error_codes
from ...core.units import (
    AreaUnits,
    DistanceUnits,
    MeasurementUnits,
    VolumeUnits,
    WeightUnits,
)
from ...csv import error_codes as csv_error_codes
from ...discount import error_codes as discount_error_codes
from ...giftcard import error_codes as giftcard_error_codes
from ...invoice import error_codes as invoice_error_codes
from ...menu import error_codes as menu_error_codes
from ...order import error_codes as order_error_codes
from ...page import error_codes as page_error_codes
from ...payment import error_codes as payment_error_codes
from ...permission.enums import get_permissions_enum_list
from ...plugins import error_codes as plugin_error_codes
from ...product import error_codes as product_error_codes
from ...shipping import error_codes as shipping_error_codes
from ...site import error_codes as site_error_codes
from ...thumbnail import IconThumbnailFormat, ThumbnailFormat
from ...translations import error_codes as translatable_error_codes
from ...warehouse import error_codes as warehouse_error_codes
from ...webhook import error_codes as webhook_error_codes
from ..directives import doc
from ..notifications import error_codes as external_notifications_error_codes
from .doc_category import (
    DOC_CATEGORY_APPS,
    DOC_CATEGORY_ATTRIBUTES,
    DOC_CATEGORY_CHANNELS,
    DOC_CATEGORY_CHECKOUT,
    DOC_CATEGORY_DISCOUNTS,
    DOC_CATEGORY_GIFT_CARDS,
    DOC_CATEGORY_ORDERS,
    DOC_CATEGORY_PAGES,
    DOC_CATEGORY_PAYMENTS,
    DOC_CATEGORY_PRODUCTS,
    DOC_CATEGORY_SHIPPING,
    DOC_CATEGORY_USERS,
    DOC_CATEGORY_WEBHOOKS,
)
from .utils import str_to_enum


class OrderDirection(graphene.Enum):
    ASC = ""
    DESC = "-"

    @property
    def description(self):
        # Disable all the no-member violations in this function
        # pylint: disable=no-member
        if self == OrderDirection.ASC:
            return "Specifies an ascending sort order."
        if self == OrderDirection.DESC:
            return "Specifies a descending sort order."
        raise ValueError(f"Unsupported enum value: {self.value}")


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

    deprecation_reason = getattr(enum_cls, "__deprecation_reason__", None)
    if deprecation_reason:
        options.setdefault("deprecation_reason", deprecation_reason)

    type_name = type_name or (enum_cls.__name__ + "Enum")
    enum_data = [(str_to_enum(code.upper()), code) for code, name in enum_cls.CHOICES]
    return graphene.Enum(type_name, enum_data, **options)


LanguageCodeEnum = graphene.Enum(
    "LanguageCodeEnum",
    [(lang[0].replace("-", "_").upper(), lang[0]) for lang in settings.LANGUAGES],
)


JobStatusEnum = to_enum(JobStatus)

PermissionEnum = doc(
    DOC_CATEGORY_USERS,
    graphene.Enum("PermissionEnum", get_permissions_enum_list()),
)

TimePeriodTypeEnum = to_enum(TimePeriodType)
ThumbnailFormatEnum = to_enum(ThumbnailFormat)
IconThumbnailFormatEnum = to_enum(
    IconThumbnailFormat,
    type_name="IconThumbnailFormatEnum",
    description=IconThumbnailFormat.__doc__,
)

# unit enums
MeasurementUnitsEnum = to_enum(MeasurementUnits)
DistanceUnitsEnum = to_enum(DistanceUnits)
AreaUnitsEnum = to_enum(AreaUnits)
VolumeUnitsEnum = to_enum(VolumeUnits)
WeightUnitsEnum = to_enum(WeightUnits)
unit_enums = [DistanceUnitsEnum, AreaUnitsEnum, VolumeUnitsEnum, WeightUnitsEnum]


class ErrorPolicy:
    IGNORE_FAILED = "ignore_failed"
    REJECT_EVERYTHING = "reject_everything"
    REJECT_FAILED_ROWS = "reject_failed_rows"

    CHOICES = [
        (IGNORE_FAILED, "Ignore failed"),
        (REJECT_EVERYTHING, "Reject everything"),
        (REJECT_FAILED_ROWS, "Reject failed rows"),
    ]


def error_policy_enum_description(enum):
    if enum == ErrorPolicyEnum.IGNORE_FAILED:
        return (
            "Save what is possible within a single row. If there are errors in an "
            "input data row, try to save it partially and skip the invalid part."
        )
    if enum == ErrorPolicyEnum.REJECT_FAILED_ROWS:
        return "Reject rows with errors."
    if enum == ErrorPolicyEnum.REJECT_EVERYTHING:
        return "Reject all rows if there is at least one error in any of them."
    return None


ErrorPolicyEnum = to_enum(ErrorPolicy, description=error_policy_enum_description)

AccountErrorCode = doc(
    DOC_CATEGORY_USERS,
    graphene.Enum.from_enum(account_error_codes.AccountErrorCode),
)

AppErrorCode = doc(
    DOC_CATEGORY_APPS, graphene.Enum.from_enum(app_error_codes.AppErrorCode)
)

AttributeErrorCode = doc(
    DOC_CATEGORY_ATTRIBUTES,
    graphene.Enum.from_enum(attribute_error_codes.AttributeErrorCode),
)

AttributeBulkCreateErrorCode = doc(
    DOC_CATEGORY_ATTRIBUTES,
    graphene.Enum.from_enum(attribute_error_codes.AttributeBulkCreateErrorCode),
)

AttributeBulkUpdateErrorCode = doc(
    DOC_CATEGORY_ATTRIBUTES,
    graphene.Enum.from_enum(attribute_error_codes.AttributeBulkUpdateErrorCode),
)

AttributeTranslateErrorCode = doc(
    DOC_CATEGORY_ATTRIBUTES,
    graphene.Enum.from_enum(translatable_error_codes.AttributeTranslateErrorCode),
)

AttributeValueTranslateErrorCode = doc(
    DOC_CATEGORY_ATTRIBUTES,
    graphene.Enum.from_enum(translatable_error_codes.AttributeValueTranslateErrorCode),
)

ChannelErrorCode = doc(
    DOC_CATEGORY_CHANNELS,
    graphene.Enum.from_enum(channel_error_codes.ChannelErrorCode),
)

CheckoutErrorCode = doc(
    DOC_CATEGORY_CHECKOUT,
    graphene.Enum.from_enum(checkout_error_codes.CheckoutErrorCode),
)

CustomerBulkUpdateErrorCode = doc(
    DOC_CATEGORY_USERS,
    graphene.Enum.from_enum(account_error_codes.CustomerBulkUpdateErrorCode),
)

ExternalNotificationTriggerErrorCode = graphene.Enum.from_enum(
    external_notifications_error_codes.ExternalNotificationErrorCodes
)
ExportErrorCode = graphene.Enum.from_enum(csv_error_codes.ExportErrorCode)

DiscountErrorCode = doc(
    DOC_CATEGORY_DISCOUNTS,
    graphene.Enum.from_enum(discount_error_codes.DiscountErrorCode),
)

VoucherCodeBulkDeleteErrorCode = doc(
    DOC_CATEGORY_DISCOUNTS,
    graphene.Enum.from_enum(discount_error_codes.VoucherCodeBulkDeleteErrorCode),
)

PluginErrorCode = graphene.Enum.from_enum(plugin_error_codes.PluginErrorCode)

GiftCardErrorCode = doc(
    DOC_CATEGORY_GIFT_CARDS,
    graphene.Enum.from_enum(giftcard_error_codes.GiftCardErrorCode),
)

MenuErrorCode = graphene.Enum.from_enum(menu_error_codes.MenuErrorCode)

OrderSettingsErrorCode = doc(
    DOC_CATEGORY_ORDERS,
    graphene.Enum.from_enum(site_error_codes.OrderSettingsErrorCode),
)

GiftCardSettingsErrorCode = doc(
    DOC_CATEGORY_GIFT_CARDS,
    graphene.Enum.from_enum(site_error_codes.GiftCardSettingsErrorCode),
)

MetadataErrorCode = graphene.Enum.from_enum(core_error_codes.MetadataErrorCode)

OrderErrorCode = doc(
    DOC_CATEGORY_ORDERS, graphene.Enum.from_enum(order_error_codes.OrderErrorCode)
)

OrderBulkCreateErrorCode = graphene.Enum.from_enum(
    order_error_codes.OrderBulkCreateErrorCode
)

InvoiceErrorCode = doc(
    DOC_CATEGORY_ORDERS,
    graphene.Enum.from_enum(invoice_error_codes.InvoiceErrorCode),
)

PageErrorCode = doc(
    DOC_CATEGORY_PAGES, graphene.Enum.from_enum(page_error_codes.PageErrorCode)
)

PaymentErrorCode = doc(
    DOC_CATEGORY_PAYMENTS, graphene.Enum.from_enum(payment_error_codes.PaymentErrorCode)
)

ProductTranslateErrorCode = doc(
    DOC_CATEGORY_PRODUCTS,
    graphene.Enum.from_enum(translatable_error_codes.ProductTranslateErrorCode),
)

ProductVariantTranslateErrorCode = doc(
    DOC_CATEGORY_PRODUCTS,
    graphene.Enum.from_enum(translatable_error_codes.ProductVariantTranslateErrorCode),
)

TransactionCreateErrorCode = doc(
    DOC_CATEGORY_PAYMENTS,
    graphene.Enum.from_enum(payment_error_codes.TransactionCreateErrorCode),
)

TransactionUpdateErrorCode = doc(
    DOC_CATEGORY_PAYMENTS,
    graphene.Enum.from_enum(payment_error_codes.TransactionUpdateErrorCode),
)

TransactionRequestActionErrorCode = doc(
    DOC_CATEGORY_PAYMENTS,
    graphene.Enum.from_enum(payment_error_codes.TransactionRequestActionErrorCode),
)

TransactionRequestRefundForGrantedRefundErrorCode = doc(
    DOC_CATEGORY_PAYMENTS,
    graphene.Enum.from_enum(
        payment_error_codes.TransactionRequestRefundForGrantedRefundErrorCode
    ),
)

TransactionEventReportErrorCode = doc(
    DOC_CATEGORY_PAYMENTS,
    graphene.Enum.from_enum(payment_error_codes.TransactionEventReportErrorCode),
)

TransactionInitializeErrorCode = doc(
    DOC_CATEGORY_PAYMENTS,
    graphene.Enum.from_enum(payment_error_codes.TransactionInitializeErrorCode),
)

TransactionProcessErrorCode = doc(
    DOC_CATEGORY_PAYMENTS,
    graphene.Enum.from_enum(payment_error_codes.TransactionProcessErrorCode),
)

PaymentGatewayConfigErrorCode = doc(
    DOC_CATEGORY_PAYMENTS,
    graphene.Enum.from_enum(payment_error_codes.PaymentGatewayConfigErrorCode),
)

PaymentGatewayInitializeErrorCode = doc(
    DOC_CATEGORY_PAYMENTS,
    graphene.Enum.from_enum(payment_error_codes.PaymentGatewayInitializeErrorCode),
)

StoredPaymentMethodRequestDeleteErrorCode = doc(
    DOC_CATEGORY_PAYMENTS,
    graphene.Enum.from_enum(
        payment_error_codes.StoredPaymentMethodRequestDeleteErrorCode
    ),
)

PaymentGatewayInitializeTokenizationErrorCode = doc(
    DOC_CATEGORY_PAYMENTS,
    graphene.Enum.from_enum(
        payment_error_codes.PaymentGatewayInitializeTokenizationErrorCode
    ),
)

PaymentMethodInitializeTokenizationErrorCode = doc(
    DOC_CATEGORY_PAYMENTS,
    graphene.Enum.from_enum(
        payment_error_codes.PaymentMethodInitializeTokenizationErrorCode
    ),
)

PaymentMethodProcessTokenizationErrorCode = doc(
    DOC_CATEGORY_PAYMENTS,
    graphene.Enum.from_enum(
        payment_error_codes.PaymentMethodProcessTokenizationErrorCode
    ),
)

PermissionGroupErrorCode = doc(
    DOC_CATEGORY_USERS,
    graphene.Enum.from_enum(account_error_codes.PermissionGroupErrorCode),
)

ProductErrorCode = doc(
    DOC_CATEGORY_PRODUCTS,
    graphene.Enum.from_enum(product_error_codes.ProductErrorCode),
)

ProductBulkCreateErrorCode = doc(
    DOC_CATEGORY_PRODUCTS,
    graphene.Enum.from_enum(product_error_codes.ProductBulkCreateErrorCode),
)

ProductBulkCreateErrorCode = doc(
    DOC_CATEGORY_PRODUCTS,
    graphene.Enum.from_enum(product_error_codes.ProductBulkCreateErrorCode),
)

ProductVariantBulkErrorCode = doc(
    DOC_CATEGORY_PRODUCTS,
    graphene.Enum.from_enum(product_error_codes.ProductVariantBulkErrorCode),
)

CollectionErrorCode = doc(
    DOC_CATEGORY_PRODUCTS,
    graphene.Enum.from_enum(product_error_codes.CollectionErrorCode),
)

SendConfirmationEmailErrorCode = doc(
    DOC_CATEGORY_USERS,
    graphene.Enum.from_enum(account_error_codes.SendConfirmationEmailErrorCode),
)

ShopErrorCode = graphene.Enum.from_enum(core_error_codes.ShopErrorCode)

ShippingErrorCode = doc(
    DOC_CATEGORY_SHIPPING,
    graphene.Enum.from_enum(shipping_error_codes.ShippingErrorCode),
)

StockErrorCode = doc(
    DOC_CATEGORY_PRODUCTS,
    graphene.Enum.from_enum(warehouse_error_codes.StockErrorCode),
)

StockBulkUpdateErrorCode = doc(
    DOC_CATEGORY_PRODUCTS,
    graphene.Enum.from_enum(warehouse_error_codes.StockBulkUpdateErrorCode),
)

UploadErrorCode = graphene.Enum.from_enum(core_error_codes.UploadErrorCode)

WarehouseErrorCode = doc(
    DOC_CATEGORY_PRODUCTS,
    graphene.Enum.from_enum(warehouse_error_codes.WarehouseErrorCode),
)

TranslationErrorCode = graphene.Enum.from_enum(core_error_codes.TranslationErrorCode)

WebhookErrorCode = doc(
    DOC_CATEGORY_WEBHOOKS, graphene.Enum.from_enum(webhook_error_codes.WebhookErrorCode)
)

WebhookDryRunErrorCode = doc(
    DOC_CATEGORY_WEBHOOKS,
    graphene.Enum.from_enum(webhook_error_codes.WebhookDryRunErrorCode),
)

WebhookTriggerErrorCode = doc(
    DOC_CATEGORY_WEBHOOKS,
    graphene.Enum.from_enum(webhook_error_codes.WebhookTriggerErrorCode),
)

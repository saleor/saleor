from typing import TYPE_CHECKING
from urllib.parse import unquote, urlparse

import graphene
from django.core.files.storage import default_storage

from ....core.utils import build_absolute_uri
from ...account.enums import AddressTypeEnum
from ...core.doc_category import (
    DOC_CATEGORY_APPS,
    DOC_CATEGORY_ATTRIBUTES,
    DOC_CATEGORY_AUTH,
    DOC_CATEGORY_CHANNELS,
    DOC_CATEGORY_CHECKOUT,
    DOC_CATEGORY_DISCOUNTS,
    DOC_CATEGORY_GIFT_CARDS,
    DOC_CATEGORY_MENU,
    DOC_CATEGORY_ORDERS,
    DOC_CATEGORY_PAGES,
    DOC_CATEGORY_PAYMENTS,
    DOC_CATEGORY_PRODUCTS,
    DOC_CATEGORY_SHIPPING,
    DOC_CATEGORY_SHOP,
    DOC_CATEGORY_TAXES,
    DOC_CATEGORY_USERS,
    DOC_CATEGORY_WEBHOOKS,
)
from ...core.scalars import Decimal
from ..descriptions import (
    ADDED_IN_36,
    ADDED_IN_312,
    ADDED_IN_314,
    DEPRECATED_IN_3X_FIELD,
    PREVIEW_FEATURE,
)
from ..enums import (
    AccountErrorCode,
    AppErrorCode,
    AttributeBulkCreateErrorCode,
    AttributeBulkUpdateErrorCode,
    AttributeErrorCode,
    AttributeTranslateErrorCode,
    AttributeValueTranslateErrorCode,
    ChannelErrorCode,
    CheckoutErrorCode,
    CollectionErrorCode,
    CustomerBulkUpdateErrorCode,
    DiscountErrorCode,
    ExportErrorCode,
    ExternalNotificationTriggerErrorCode,
    GiftCardErrorCode,
    GiftCardSettingsErrorCode,
    IconThumbnailFormatEnum,
    InvoiceErrorCode,
    JobStatusEnum,
    LanguageCodeEnum,
    MenuErrorCode,
    MetadataErrorCode,
    OrderBulkCreateErrorCode,
    OrderErrorCode,
    OrderSettingsErrorCode,
    PageErrorCode,
    PaymentErrorCode,
    PaymentGatewayConfigErrorCode,
    PaymentGatewayInitializeErrorCode,
    PaymentGatewayInitializeTokenizationErrorCode,
    PaymentMethodInitializeTokenizationErrorCode,
    PaymentMethodProcessTokenizationErrorCode,
    PermissionEnum,
    PermissionGroupErrorCode,
    PluginErrorCode,
    ProductBulkCreateErrorCode,
    ProductErrorCode,
    ProductTranslateErrorCode,
    ProductVariantBulkErrorCode,
    ProductVariantTranslateErrorCode,
    SendConfirmationEmailErrorCode,
    ShippingErrorCode,
    ShopErrorCode,
    StockBulkUpdateErrorCode,
    StockErrorCode,
    StoredPaymentMethodRequestDeleteErrorCode,
    ThumbnailFormatEnum,
    TimePeriodTypeEnum,
    TransactionCreateErrorCode,
    TransactionEventReportErrorCode,
    TransactionInitializeErrorCode,
    TransactionProcessErrorCode,
    TransactionRequestActionErrorCode,
    TransactionRequestRefundForGrantedRefundErrorCode,
    TransactionUpdateErrorCode,
    TranslationErrorCode,
    UploadErrorCode,
    WarehouseErrorCode,
    WebhookDryRunErrorCode,
    WebhookErrorCode,
    WebhookTriggerErrorCode,
    WeightUnitsEnum,
)
from ..scalars import Date, PositiveDecimal
from ..tracing import traced_resolver
from .base import BaseObjectType
from .money import VAT
from .upload import Upload

if TYPE_CHECKING:
    from .. import ResolveInfo

# deprecated - this is temporary constant that contains the graphql types
# which has double id available - uuid and old int id
TYPES_WITH_DOUBLE_ID_AVAILABLE = ["Order", "OrderLine", "OrderDiscount", "CheckoutLine"]


class NonNullList(graphene.List):
    """A list type that automatically adds non-null constraint on contained items."""

    def __init__(self, of_type, *args, **kwargs):
        of_type = graphene.NonNull(of_type)
        super(NonNullList, self).__init__(of_type, *args, **kwargs)


class CountryDisplay(graphene.ObjectType):
    code = graphene.String(description="Country code.", required=True)
    country = graphene.String(description="Country name.", required=True)
    vat = graphene.Field(
        VAT,
        description="Country tax.",
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Always returns `null`. Use `TaxClassCountryRate`"
            " type to manage tax rates per country."
        ),
    )


class LanguageDisplay(graphene.ObjectType):
    code = LanguageCodeEnum(
        description="ISO 639 representation of the language name.", required=True
    )
    language = graphene.String(description="Full name of the language.", required=True)


class Permission(BaseObjectType):
    code = PermissionEnum(description="Internal code for permission.", required=True)
    name = graphene.String(
        description="Describe action(s) allowed to do by permission.", required=True
    )

    class Meta:
        doc_category = DOC_CATEGORY_AUTH
        description = "Represents a permission object in a friendly form."


class Error(BaseObjectType):
    field = graphene.String(
        description=(
            "Name of a field that caused the error. A value of `null` indicates that "
            "the error isn't associated with a particular field."
        ),
        required=False,
    )
    message = graphene.String(description="The error message.")

    class Meta:
        description = "Represents an error in the input of a mutation."


class BulkError(BaseObjectType):
    path = graphene.String(
        description=(
            "Path to field that caused the error. A value of `null` indicates that "
            "the error isn't associated with a particular field."
        ),
        required=False,
    )
    message = graphene.String(description="The error message.")

    class Meta:
        description = "Represents an error in the input of a mutation."


class AccountError(Error):
    code = AccountErrorCode(description="The error code.", required=True)
    address_type = AddressTypeEnum(  # type: ignore[has-type]
        description="A type of address that causes the error.", required=False
    )

    class Meta:
        description = "Represents errors in account mutations."
        doc_category = DOC_CATEGORY_USERS


class SendConfirmationEmailError(Error):
    code = SendConfirmationEmailErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_USERS


class AppError(Error):
    code = AppErrorCode(description="The error code.", required=True)
    permissions = NonNullList(
        PermissionEnum,
        description="List of permissions which causes the error.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_APPS


class AttributeError(Error):
    code = AttributeErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES


class StaffError(AccountError):
    permissions = NonNullList(
        PermissionEnum,
        description="List of permissions which causes the error.",
        required=False,
    )
    groups = NonNullList(
        graphene.ID,
        description="List of permission group IDs which cause the error.",
        required=False,
    )
    users = NonNullList(
        graphene.ID,
        description="List of user IDs which causes the error.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_USERS


class ChannelError(Error):
    code = ChannelErrorCode(description="The error code.", required=True)
    shipping_zones = NonNullList(
        graphene.ID,
        description="List of shipping zone IDs which causes the error.",
        required=False,
    )
    warehouses = NonNullList(
        graphene.ID,
        description="List of warehouses IDs which causes the error.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_CHANNELS


class CheckoutError(Error):
    code = CheckoutErrorCode(description="The error code.", required=True)
    variants = NonNullList(
        graphene.ID,
        description="List of varint IDs which causes the error.",
        required=False,
    )
    lines = NonNullList(
        graphene.ID,
        description="List of line Ids which cause the error.",
        required=False,
    )
    address_type = AddressTypeEnum(  # type: ignore[has-type]
        description="A type of address that causes the error.", required=False
    )

    class Meta:
        doc_category = DOC_CATEGORY_CHECKOUT


class CustomerBulkUpdateError(BulkError):
    code = CustomerBulkUpdateErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_USERS


class ProductWithoutVariantError(Error):
    products = NonNullList(
        graphene.ID,
        description="List of products IDs which causes the error.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class DiscountError(ProductWithoutVariantError):
    code = DiscountErrorCode(description="The error code.", required=True)
    channels = NonNullList(
        graphene.ID,
        description="List of channels IDs which causes the error.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS


class ExportError(Error):
    code = ExportErrorCode(description="The error code.", required=True)


class ExternalNotificationError(Error):
    code = ExternalNotificationTriggerErrorCode(
        description="The error code.", required=True
    )


class MenuError(Error):
    code = MenuErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_MENU


class OrderSettingsError(Error):
    code = OrderSettingsErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class GiftCardSettingsError(Error):
    code = GiftCardSettingsErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_GIFT_CARDS


class MetadataError(Error):
    code = MetadataErrorCode(description="The error code.", required=True)


class OrderError(Error):
    code = OrderErrorCode(description="The error code.", required=True)
    warehouse = graphene.ID(
        description="Warehouse ID which causes the error.",
        required=False,
    )
    order_lines = NonNullList(
        graphene.ID,
        description="List of order line IDs that cause the error.",
        required=False,
    )
    variants = NonNullList(
        graphene.ID,
        description="List of product variants that are associated with the error",
        required=False,
    )
    address_type = AddressTypeEnum(  # type: ignore[has-type]
        description="A type of address that causes the error.", required=False
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderBulkCreateError(BulkError):
    code = OrderBulkCreateErrorCode(description="The error code.", required=False)

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class InvoiceError(Error):
    code = InvoiceErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class PermissionGroupError(Error):
    code = PermissionGroupErrorCode(description="The error code.", required=True)
    permissions = NonNullList(
        PermissionEnum,
        description="List of permissions which causes the error.",
        required=False,
    )
    users = NonNullList(
        graphene.ID,
        description="List of user IDs which causes the error.",
        required=False,
    )
    channels = NonNullList(
        graphene.ID,
        description="List of chnnels IDs which causes the error.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_USERS


class ProductError(Error):
    code = ProductErrorCode(description="The error code.", required=True)
    attributes = NonNullList(
        graphene.ID,
        description="List of attributes IDs which causes the error.",
        required=False,
    )
    values = NonNullList(
        graphene.ID,
        description="List of attribute values IDs which causes the error.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class CollectionError(ProductWithoutVariantError):
    code = CollectionErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductChannelListingError(ProductError):
    channels = NonNullList(
        graphene.ID,
        description="List of channels IDs which causes the error.",
        required=False,
    )
    variants = NonNullList(
        graphene.ID,
        description="List of variants IDs which causes the error.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class CollectionChannelListingError(ProductError):
    channels = NonNullList(
        graphene.ID,
        description="List of channels IDs which causes the error.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class AttributeBulkCreateError(BulkError):
    code = AttributeBulkCreateErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES


class AttributeBulkUpdateError(BulkError):
    code = AttributeBulkUpdateErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES


class BulkProductError(ProductError):
    index = graphene.Int(
        description="Index of an input list item that caused the error."
    )
    warehouses = NonNullList(
        graphene.ID,
        description="List of warehouse IDs which causes the error.",
        required=False,
    )
    channels = NonNullList(
        graphene.ID,
        description="List of channel IDs which causes the error.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductBulkCreateError(BulkError):
    code = ProductBulkCreateErrorCode(description="The error code.", required=True)
    attributes = NonNullList(
        graphene.ID,
        description="List of attributes IDs which causes the error.",
        required=False,
    )
    values = NonNullList(
        graphene.ID,
        description="List of attribute values IDs which causes the error.",
        required=False,
    )
    warehouses = NonNullList(
        graphene.ID,
        description="List of warehouse IDs which causes the error.",
        required=False,
    )
    channels = NonNullList(
        graphene.ID,
        description="List of channel IDs which causes the error.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductVariantBulkError(Error):
    code = ProductVariantBulkErrorCode(description="The error code.", required=True)
    path = graphene.String(
        description=(
            "Path to field that caused the error. A value of `null` indicates that "
            "the error isn't associated with a particular field." + ADDED_IN_314
        ),
        required=False,
    )
    attributes = NonNullList(
        graphene.ID,
        description="List of attributes IDs which causes the error.",
        required=False,
    )
    values = NonNullList(
        graphene.ID,
        description="List of attribute values IDs which causes the error.",
        required=False,
    )
    warehouses = NonNullList(
        graphene.ID,
        description="List of warehouse IDs which causes the error.",
        required=False,
    )
    stocks = NonNullList(
        graphene.ID,
        description="List of stocks IDs which causes the error." + ADDED_IN_312,
        required=False,
    )
    channels = NonNullList(
        graphene.ID,
        description="List of channel IDs which causes the error." + ADDED_IN_312,
        required=False,
    )
    channel_listings = NonNullList(
        graphene.ID,
        description="List of channel listings IDs which causes the error.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ShopError(Error):
    code = ShopErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_SHOP


class ShippingError(Error):
    code = ShippingErrorCode(description="The error code.", required=True)
    warehouses = NonNullList(
        graphene.ID,
        description="List of warehouse IDs which causes the error.",
        required=False,
    )
    channels = NonNullList(
        graphene.ID,
        description="List of channels IDs which causes the error.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_SHIPPING


class PageError(Error):
    code = PageErrorCode(description="The error code.", required=True)
    attributes = NonNullList(
        graphene.ID,
        description="List of attributes IDs which causes the error.",
        required=False,
    )
    values = NonNullList(
        graphene.ID,
        description="List of attribute values IDs which causes the error.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PAGES


class PaymentError(Error):
    code = PaymentErrorCode(description="The error code.", required=True)
    variants = NonNullList(
        graphene.ID,
        description="List of variant IDs which causes the error.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class ProductBulkTranslateError(BulkError):
    code = ProductTranslateErrorCode(description="The error code.", required=True)


class ProductVariantBulkTranslateError(BulkError):
    code = ProductVariantTranslateErrorCode(
        description="The error code.", required=True
    )


class TransactionCreateError(Error):
    code = TransactionCreateErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class TransactionUpdateError(Error):
    code = TransactionUpdateErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class TransactionRequestActionError(Error):
    code = TransactionRequestActionErrorCode(
        description="The error code.", required=True
    )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class TransactionRequestRefundForGrantedRefundError(Error):
    code = TransactionRequestRefundForGrantedRefundErrorCode(
        description="The error code.", required=True
    )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class TransactionEventReportError(Error):
    code = TransactionEventReportErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class TransactionInitializeError(Error):
    code = TransactionInitializeErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class TransactionProcessError(Error):
    code = TransactionProcessErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class PaymentGatewayConfigError(Error):
    code = PaymentGatewayConfigErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class PaymentGatewayInitializeError(Error):
    code = PaymentGatewayInitializeErrorCode(
        description="The error code.", required=True
    )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class PaymentMethodRequestDeleteError(Error):
    code = StoredPaymentMethodRequestDeleteErrorCode(
        description="The error code.", required=True
    )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class PaymentGatewayInitializeTokenizationError(Error):
    code = PaymentGatewayInitializeTokenizationErrorCode(
        description="The error code.", required=True
    )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class PaymentMethodInitializeTokenizationError(Error):
    code = PaymentMethodInitializeTokenizationErrorCode(
        description="The error code.", required=True
    )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class PaymentMethodProcessTokenizationError(Error):
    code = PaymentMethodProcessTokenizationErrorCode(
        description="The error code.", required=True
    )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class GiftCardError(Error):
    code = GiftCardErrorCode(description="The error code.", required=True)
    tags = NonNullList(
        graphene.String,
        description="List of tag values that cause the error.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_GIFT_CARDS


class PluginError(Error):
    code = PluginErrorCode(description="The error code.", required=True)


class StockError(Error):
    code = StockErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class BulkStockError(ProductError):
    index = graphene.Int(
        description="Index of an input list item that caused the error."
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class StockBulkUpdateError(Error):
    code = StockBulkUpdateErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class UploadError(Error):
    code = UploadErrorCode(description="The error code.", required=True)


class WarehouseError(Error):
    code = WarehouseErrorCode(description="The error code.", required=True)
    shipping_zones = NonNullList(
        graphene.ID,
        description="List of shipping zones IDs which causes the error.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class WebhookError(Error):
    code = WebhookErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_WEBHOOKS


class WebhookDryRunError(Error):
    code = WebhookDryRunErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_WEBHOOKS


class WebhookTriggerError(Error):
    code = WebhookTriggerErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_WEBHOOKS


class TranslationError(Error):
    code = TranslationErrorCode(description="The error code.", required=True)


class TranslationBulkError(BulkError):
    code = TranslationErrorCode(description="The error code.", required=True)


class SeoInput(graphene.InputObjectType):
    title = graphene.String(description="SEO title.")
    description = graphene.String(description="SEO description.")


class AttributeBulkTranslateError(BulkError):
    code = AttributeTranslateErrorCode(description="The error code.", required=True)


class AttributeValueBulkTranslateError(BulkError):
    code = AttributeValueTranslateErrorCode(
        description="The error code.", required=True
    )


class Weight(graphene.ObjectType):
    unit = WeightUnitsEnum(description="Weight unit.", required=True)
    value = graphene.Float(description="Weight value.", required=True)

    class Meta:
        description = "Represents weight value in a specific weight unit."


class Image(graphene.ObjectType):
    url = graphene.String(required=True, description="The URL of the image.")
    alt = graphene.String(description="Alt text for an image.")

    class Meta:
        description = "Represents an image."

    def resolve_url(root, _info: "ResolveInfo"):
        if urlparse(root.url).netloc:
            return root.url
        return build_absolute_uri(root.url)


class File(graphene.ObjectType):
    url = graphene.String(required=True, description="The URL of the file.")
    content_type = graphene.String(
        required=False, description="Content type of the file."
    )

    @staticmethod
    def resolve_url(root, _info: "ResolveInfo"):
        # check if URL is absolute:
        if urlparse(root.url).netloc:
            return root.url
        # unquote used for preventing double URL encoding
        return build_absolute_uri(default_storage.url(unquote(root.url)))


class PriceInput(graphene.InputObjectType):
    currency = graphene.String(description="Currency code.", required=True)
    amount = PositiveDecimal(description="Amount of money.", required=True)


class PriceRangeInput(graphene.InputObjectType):
    gte = graphene.Float(description="Price greater than or equal to.", required=False)
    lte = graphene.Float(description="Price less than or equal to.", required=False)


class DecimalRangeInput(graphene.InputObjectType):
    gte = Decimal(description="Decimal value greater than or equal to.", required=False)
    lte = Decimal(description="Decimal value less than or equal to.", required=False)


class DateRangeInput(graphene.InputObjectType):
    gte = Date(description="Start date.", required=False)
    lte = Date(description="End date.", required=False)


class DateTimeRangeInput(graphene.InputObjectType):
    gte = graphene.DateTime(description="Start date.", required=False)
    lte = graphene.DateTime(description="End date.", required=False)


class IntRangeInput(graphene.InputObjectType):
    gte = graphene.Int(description="Value greater than or equal to.", required=False)
    lte = graphene.Int(description="Value less than or equal to.", required=False)


class TimePeriodInputType(graphene.InputObjectType):
    amount = graphene.Int(description="The length of the period.", required=True)
    type = TimePeriodTypeEnum(description="The type of the period.", required=True)


class TaxType(BaseObjectType):
    """Representation of tax types fetched from tax gateway."""

    description = graphene.String(description="Description of the tax type.")
    tax_code = graphene.String(
        description="External tax code used to identify given tax group."
    )

    class Meta:
        doc_category = DOC_CATEGORY_TAXES


class Job(graphene.Interface):
    status = JobStatusEnum(description="Job status.", required=True)
    created_at = graphene.DateTime(
        description="Created date time of job in ISO 8601 format.", required=True
    )
    updated_at = graphene.DateTime(
        description="Date time of job last update in ISO 8601 format.", required=True
    )
    message = graphene.String(description="Job message.")

    @classmethod
    @traced_resolver
    def resolve_type(cls, instance, _info: "ResolveInfo"):
        """Map a data object to a Graphene type."""
        return None  # FIXME: why do we have this method?


class TimePeriod(graphene.ObjectType):
    amount = graphene.Int(description="The length of the period.", required=True)
    type = TimePeriodTypeEnum(description="The type of the period.", required=True)


class ThumbnailField(graphene.Field):
    size = graphene.Int(
        description=(
            "Desired longest side the image in pixels. Defaults to 4096. "
            "Images are never cropped. "
            "Pass 0 to retrieve the original size (not recommended)."
        ),
    )
    format = ThumbnailFormatEnum(
        default_value="ORIGINAL",
        description=(
            "The format of the image. When not provided, format of the original "
            "image will be used." + ADDED_IN_36
        ),
    )

    def __init__(self, of_type=Image, *args, **kwargs):
        kwargs["size"] = self.size
        kwargs["format"] = self.format
        super().__init__(of_type, *args, **kwargs)


class IconThumbnailField(ThumbnailField):
    format = IconThumbnailFormatEnum(
        default_value="ORIGINAL",
        description=(
            "The format of the image. When not provided, format of the original "
            "image will be used." + ADDED_IN_314 + PREVIEW_FEATURE
        ),
    )


class MediaInput(graphene.InputObjectType):
    alt = graphene.String(description="Alt text for a product media.")
    image = Upload(
        required=False, description="Represents an image file in a multipart request."
    )
    media_url = graphene.String(
        required=False, description="Represents an URL to an external media."
    )

from urllib.parse import urljoin

import graphene
from django.conf import settings

from ....core.tracing import traced_resolver
from ....product.product_images import get_thumbnail
from ...account.enums import AddressTypeEnum
from ..enums import (
    AccountErrorCode,
    AppErrorCode,
    AttributeErrorCode,
    ChannelErrorCode,
    CheckoutErrorCode,
    CollectionErrorCode,
    DiscountErrorCode,
    ExportErrorCode,
    ExternalNotificationTriggerErrorCode,
    GiftCardErrorCode,
    GiftCardSettingsErrorCode,
    InvoiceErrorCode,
    JobStatusEnum,
    LanguageCodeEnum,
    MenuErrorCode,
    MetadataErrorCode,
    OrderErrorCode,
    OrderSettingsErrorCode,
    PageErrorCode,
    PaymentErrorCode,
    PermissionEnum,
    PermissionGroupErrorCode,
    PluginErrorCode,
    ProductErrorCode,
    ShippingErrorCode,
    ShopErrorCode,
    StockErrorCode,
    TimePeriodTypeEnum,
    TransactionCreateErrorCode,
    TransactionRequestActionErrorCode,
    TransactionUpdateErrorCode,
    TranslationErrorCode,
    UploadErrorCode,
    WarehouseErrorCode,
    WebhookErrorCode,
    WeightUnitsEnum,
)
from ..scalars import PositiveDecimal
from .money import VAT

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
    vat = graphene.Field(VAT, description="Country tax.")


class LanguageDisplay(graphene.ObjectType):
    code = LanguageCodeEnum(
        description="ISO 639 representation of the language name.", required=True
    )
    language = graphene.String(description="Full name of the language.", required=True)


class Permission(graphene.ObjectType):
    code = PermissionEnum(description="Internal code for permission.", required=True)
    name = graphene.String(
        description="Describe action(s) allowed to do by permission.", required=True
    )

    class Meta:
        description = "Represents a permission object in a friendly form."


class Error(graphene.ObjectType):
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


class AccountError(Error):
    code = AccountErrorCode(description="The error code.", required=True)
    address_type = AddressTypeEnum(
        description="A type of address that causes the error.", required=False
    )


class AppError(Error):
    code = AppErrorCode(description="The error code.", required=True)
    permissions = NonNullList(
        PermissionEnum,
        description="List of permissions which causes the error.",
        required=False,
    )


class AttributeError(Error):
    code = AttributeErrorCode(description="The error code.", required=True)


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


class ChannelError(Error):
    code = ChannelErrorCode(description="The error code.", required=True)
    shipping_zones = NonNullList(
        graphene.ID,
        description="List of shipping zone IDs which causes the error.",
        required=False,
    )


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
    address_type = AddressTypeEnum(
        description="A type of address that causes the error.", required=False
    )


class ProductWithoutVariantError(Error):
    products = NonNullList(
        graphene.ID,
        description="List of products IDs which causes the error.",
    )


class DiscountError(ProductWithoutVariantError):
    code = DiscountErrorCode(description="The error code.", required=True)
    channels = NonNullList(
        graphene.ID,
        description="List of channels IDs which causes the error.",
        required=False,
    )


class ExportError(Error):
    code = ExportErrorCode(description="The error code.", required=True)


class ExternalNotificationError(Error):
    code = ExternalNotificationTriggerErrorCode(
        description="The error code.", required=True
    )


class MenuError(Error):
    code = MenuErrorCode(description="The error code.", required=True)


class OrderSettingsError(Error):
    code = OrderSettingsErrorCode(description="The error code.", required=True)


class GiftCardSettingsError(Error):
    code = GiftCardSettingsErrorCode(description="The error code.", required=True)


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
    address_type = AddressTypeEnum(
        description="A type of address that causes the error.", required=False
    )


class InvoiceError(Error):
    code = InvoiceErrorCode(description="The error code.", required=True)


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


class CollectionError(ProductWithoutVariantError):
    code = CollectionErrorCode(description="The error code.", required=True)


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


class CollectionChannelListingError(ProductError):
    channels = NonNullList(
        graphene.ID,
        description="List of channels IDs which causes the error.",
        required=False,
    )


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


class ShopError(Error):
    code = ShopErrorCode(description="The error code.", required=True)


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


class PaymentError(Error):
    code = PaymentErrorCode(description="The error code.", required=True)
    variants = NonNullList(
        graphene.ID,
        description="List of varint IDs which causes the error.",
        required=False,
    )


class TransactionCreateError(Error):
    code = TransactionCreateErrorCode(description="The error code.", required=True)


class TransactionUpdateError(Error):
    code = TransactionUpdateErrorCode(description="The error code.", required=True)


class TransactionRequestActionError(Error):
    code = TransactionRequestActionErrorCode(
        description="The error code.", required=True
    )


class GiftCardError(Error):
    code = GiftCardErrorCode(description="The error code.", required=True)
    tags = NonNullList(
        graphene.String,
        description="List of tag values that cause the error.",
        required=False,
    )


class PluginError(Error):
    code = PluginErrorCode(description="The error code.", required=True)


class StockError(Error):
    code = StockErrorCode(description="The error code.", required=True)


class BulkStockError(ProductError):
    index = graphene.Int(
        description="Index of an input list item that caused the error."
    )


class UploadError(Error):
    code = UploadErrorCode(description="The error code.", required=True)


class WarehouseError(Error):
    code = WarehouseErrorCode(description="The error code.", required=True)


class WebhookError(Error):
    code = WebhookErrorCode(description="The error code.", required=True)


class TranslationError(Error):
    code = TranslationErrorCode(description="The error code.", required=True)


class SeoInput(graphene.InputObjectType):
    title = graphene.String(description="SEO title.")
    description = graphene.String(description="SEO description.")


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

    @staticmethod
    def get_adjusted(image, alt, size, rendition_key_set, info):
        """Return Image adjusted with given size."""
        if size:
            url = get_thumbnail(
                image_file=image,
                size=size,
                method="thumbnail",
                rendition_key_set=rendition_key_set,
            )
        else:
            url = image.url
        url = info.context.build_absolute_uri(url)
        return Image(url, alt)


class File(graphene.ObjectType):
    url = graphene.String(required=True, description="The URL of the file.")
    content_type = graphene.String(
        required=False, description="Content type of the file."
    )

    @staticmethod
    def resolve_url(root, info):
        return info.context.build_absolute_uri(urljoin(settings.MEDIA_URL, root.url))


class PriceInput(graphene.InputObjectType):
    currency = graphene.String(description="Currency code.", required=True)
    amount = PositiveDecimal(description="Amount of money.", required=True)


class PriceRangeInput(graphene.InputObjectType):
    gte = graphene.Float(description="Price greater than or equal to.", required=False)
    lte = graphene.Float(description="Price less than or equal to.", required=False)


class DateRangeInput(graphene.InputObjectType):
    gte = graphene.Date(description="Start date.", required=False)
    lte = graphene.Date(description="End date.", required=False)


class DateTimeRangeInput(graphene.InputObjectType):
    gte = graphene.DateTime(description="Start date.", required=False)
    lte = graphene.DateTime(description="End date.", required=False)


class IntRangeInput(graphene.InputObjectType):
    gte = graphene.Int(description="Value greater than or equal to.", required=False)
    lte = graphene.Int(description="Value less than or equal to.", required=False)


class TimePeriodInputType(graphene.InputObjectType):
    amount = graphene.Int(description="The length of the period.", required=True)
    type = TimePeriodTypeEnum(description="The type of the period.", required=True)


class TaxType(graphene.ObjectType):
    """Representation of tax types fetched from tax gateway."""

    description = graphene.String(description="Description of the tax type.")
    tax_code = graphene.String(
        description="External tax code used to identify given tax group."
    )


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
    def resolve_type(cls, instance, _info):
        """Map a data object to a Graphene type."""
        MODEL_TO_TYPE_MAP = {
            # <DjangoModel>: <GrapheneType>
        }
        return MODEL_TO_TYPE_MAP.get(type(instance))


class TimePeriod(graphene.ObjectType):
    amount = graphene.Int(description="The length of the period.", required=True)
    type = TimePeriodTypeEnum(description="The type of the period.", required=True)

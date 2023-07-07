import graphene
from graphene import relay

from ....product import models
from ...channel import ChannelContext
from ...core import ResolveInfo
from ...core.connection import CountableConnection
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.scalars import UUID
from ...core.types import ModelObjectType, NonNullList
from ...meta.types import ObjectWithMetadata
from ..dataloaders import ProductVariantByIdLoader


class DigitalContentUrl(ModelObjectType[models.DigitalContentUrl]):
    id = graphene.GlobalID(
        required=True, description="The ID of the digital content URL."
    )
    content = graphene.Field(
        lambda: DigitalContent,
        required=True,
        description="Digital content associated with the URL.",
    )
    created = graphene.DateTime(
        required=True,
        description="Date and time when the digital content URL was created.",
    )
    download_num = graphene.Int(
        required=True,
        description="Number of times digital content has been downloaded.",
    )
    url = graphene.String(description="URL for digital content.")
    token = graphene.Field(UUID, description="UUID of digital content.", required=True)

    class Meta:
        model = models.DigitalContentUrl
        interfaces = (relay.Node,)
        description = "Represents a URL for digital content."

    @staticmethod
    def resolve_created(root: models.DigitalContentUrl, _info):
        return root.created_at

    @staticmethod
    def resolve_url(root: models.DigitalContentUrl, *_args):
        return root.get_absolute_url()


class DigitalContent(ModelObjectType[models.DigitalContent]):
    id = graphene.GlobalID(required=True, description="The ID of the digital content.")
    use_default_settings = graphene.Boolean(
        required=True,
        description="Default settings indicator for digital content.",
    )
    automatic_fulfillment = graphene.Boolean(
        required=True,
        description="Indicator for automatic fulfillment of digital content.",
    )
    content_file = graphene.String(
        required=True, description="File associated with digital content."
    )
    max_downloads = graphene.Int(
        description="Maximum number of allowed downloads for the digital content."
    )
    url_valid_days = graphene.Int(
        description="Number of days the URL for the digital content remains valid."
    )
    urls = NonNullList(
        lambda: DigitalContentUrl,
        description="List of URLs for the digital variant.",
    )
    product_variant = graphene.Field(
        "saleor.graphql.product.types.products.ProductVariant",
        required=True,
        description="Product variant assigned to digital content.",
    )

    class Meta:
        model = models.DigitalContent
        interfaces = (relay.Node, ObjectWithMetadata)
        description = "Represents digital content associated with a product variant."

    @staticmethod
    def resolve_urls(root: models.DigitalContent, _info):
        return root.urls.all()

    @staticmethod
    def resolve_product_variant(root: models.DigitalContent, info: ResolveInfo):
        return (
            ProductVariantByIdLoader(info.context)
            .load(root.product_variant_id)
            .then(lambda variant: ChannelContext(node=variant, channel_slug=None))
        )


class DigitalContentCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        node = DigitalContent
        description = "A connection to a list of digital content items."

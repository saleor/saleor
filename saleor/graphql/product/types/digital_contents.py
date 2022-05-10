import graphene
from graphene import relay

from ....product import models
from ...channel import ChannelContext
from ...core.connection import CountableConnection
from ...core.scalars import UUID
from ...core.types import ModelObjectType, NonNullList
from ...meta.types import ObjectWithMetadata
from ..dataloaders import ProductVariantByIdLoader


class DigitalContentUrl(ModelObjectType):
    id = graphene.GlobalID(required=True)
    content = graphene.Field(lambda: DigitalContent, required=True)
    created = graphene.DateTime(required=True)
    download_num = graphene.Int(required=True)
    url = graphene.String(description="URL for digital content.")
    token = graphene.Field(UUID, description="UUID of digital content.", required=True)

    class Meta:
        model = models.DigitalContentUrl
        interfaces = (relay.Node,)

    @staticmethod
    def resolve_created(root: models.DigitalContentUrl, _info):
        return root.created_at

    @staticmethod
    def resolve_url(root: models.DigitalContentUrl, *_args):
        return root.get_absolute_url()


class DigitalContent(ModelObjectType):
    id = graphene.GlobalID(required=True)
    use_default_settings = graphene.Boolean(required=True)
    automatic_fulfillment = graphene.Boolean(required=True)
    content_file = graphene.String(required=True)
    max_downloads = graphene.Int()
    url_valid_days = graphene.Int()
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

    @staticmethod
    def resolve_urls(root: models.DigitalContent, _info):
        return root.urls.all()

    @staticmethod
    def resolve_product_variant(root: models.DigitalContent, info):
        return (
            ProductVariantByIdLoader(info.context)
            .load(root.product_variant_id)
            .then(lambda variant: ChannelContext(node=variant, channel_slug=None))
        )


class DigitalContentCountableConnection(CountableConnection):
    class Meta:
        node = DigitalContent

import graphene
from graphene import relay

from ....product import models
from ...channel import ChannelContext
from ...core.connection import CountableDjangoObjectType
from ...core.scalars import UUID
from ...meta.types import ObjectWithMetadata
from ..dataloaders import ProductVariantByIdLoader


class DigitalContentUrl(CountableDjangoObjectType):
    url = graphene.String(description="URL for digital content.")
    token = graphene.Field(
        UUID, description=("UUID of digital content."), required=True
    )

    class Meta:
        model = models.DigitalContentUrl
        only_fields = ["content", "created", "download_num"]
        interfaces = (relay.Node,)

    @staticmethod
    def resolve_url(root: models.DigitalContentUrl, *_args):
        return root.get_absolute_url()


class DigitalContent(CountableDjangoObjectType):
    urls = graphene.List(
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
        only_fields = [
            "automatic_fulfillment",
            "content_file",
            "max_downloads",
            "url_valid_days",
            "urls",
            "use_default_settings",
        ]
        interfaces = (relay.Node, ObjectWithMetadata)

    @staticmethod
    def resolve_urls(root: models.DigitalContent, **_kwargs):
        return root.urls.all()

    @staticmethod
    def resolve_product_variant(root: models.DigitalContent, info):
        return (
            ProductVariantByIdLoader(info.context)
            .load(root.product_variant_id)
            .then(lambda variant: ChannelContext(node=variant, channel_slug=None))
        )

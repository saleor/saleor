import graphene
from graphene import relay

from ....product import models
from ...core.connection import CountableDjangoObjectType
from ...core.scalars import UUID
from ...meta.types import ObjectWithMetadata


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

    class Meta:
        model = models.DigitalContent
        only_fields = [
            "automatic_fulfillment",
            "content_file",
            "max_downloads",
            "product_variant",
            "url_valid_days",
            "urls",
            "use_default_settings",
        ]
        interfaces = (relay.Node, ObjectWithMetadata)

    @staticmethod
    def resolve_urls(root: models.DigitalContent, **_kwargs):
        return root.urls.all()

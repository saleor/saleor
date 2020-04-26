import graphene
from graphene import relay

from ....core.permissions import ProductPermissions
from ....product import models
from ...core.connection import CountableDjangoObjectType
from ...decorators import permission_required
from ...meta.deprecated.resolvers import resolve_meta, resolve_private_meta
from ...meta.types import ObjectWithMetadata


class DigitalContentUrl(CountableDjangoObjectType):
    url = graphene.String(description="URL for digital content.")

    class Meta:
        model = models.DigitalContentUrl
        only_fields = ["content", "created", "download_num", "token"]
        interfaces = (relay.Node,)

    @staticmethod
    def resolve_url(root: models.DigitalContentUrl, *_args):
        return root.get_absolute_url()


class DigitalContent(CountableDjangoObjectType):
    urls = graphene.List(
        lambda: DigitalContentUrl, description="List of URLs for the digital variant.",
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
    def resolve_urls(root: models.DigitalContent, info, **_kwargs):
        return root.urls.all()

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_private_meta(root: models.DigitalContent, _info):
        return resolve_private_meta(root, _info)

    @staticmethod
    def resolve_meta(root: models.DigitalContent, _info):
        return resolve_meta(root, _info)

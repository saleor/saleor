import graphene
from graphene import relay
from promise import Promise

from ...core.utils import build_absolute_uri
from ...product import MediaOwnerTypes, ProductMediaTypes, models
from ...product.media import OWNER_TYPE_TO_GRAPHQL_TYPE
from ...thumbnail.utils import (
    get_image_or_proxy_url,
    get_original_image_proxy_url,
    get_thumbnail_format,
    get_thumbnail_size,
)
from ..core.context import get_database_connection_name
from ..core.descriptions import ADDED_IN_324
from ..core.doc_category import DOC_CATEGORY_MEDIA
from ..core.federation import federated_entity, resolve_federation_references
from ..core.fields import JSONString
from ..core.types import BaseInterface, ModelObjectType, ThumbnailField
from ..meta.types import ObjectWithMetadata
from ..product.dataloaders import ThumbnailByProductMediaIdSizeAndFormatLoader
from ..product.enums import ProductMediaType
from .enums import MediaOwnerType, MediaType


class Media(BaseInterface):
    id = graphene.ID(required=True, description="The unique ID of the media.")
    sort_order = graphene.Int(description="The sort order of the media.")
    alt = graphene.String(required=True, description="The alt text of the media.")
    media_type = MediaType(
        required=True, description="The type of the media." + ADDED_IN_324
    )
    oembed_data = JSONString(required=True, description="The oEmbed data of the media.")
    url = ThumbnailField(
        graphene.String, required=True, description="The URL of the media."
    )
    owner_type = MediaOwnerType(
        required=True,
        description="The type of the entity the media belongs to." + ADDED_IN_324,
    )
    owner_id = graphene.ID(
        required=True,
        description="ID of the entity the media belongs to." + ADDED_IN_324,
    )

    class Meta:
        doc_category = DOC_CATEGORY_MEDIA
        description = (
            "Represents a media item (an image or an oEmbed video) owned by a single "
            "entity. The concrete type identifies the kind of owner.\n\n"
            "Note: `Media` does not implement `Node` or `ObjectWithMetadata`; select "
            "those fields through an inline fragment on the concrete type."
            + ADDED_IN_324
        )

    @classmethod
    def resolve_type(cls, instance: models.ProductMedia, info):
        return resolve_media_type_for_owner(instance)


class MediaResolvers:
    """Shared resolvers for every concrete `Media` type.

    The GraphQL type name is baked into thumbnail proxy URLs, so each subclass
    resolves `url` under its own name.
    """

    # Owner type this concrete media type is keyed to; set by every subclass.
    owner_type: str

    @classmethod
    def get_node(cls, _, id) -> models.ProductMedia | None:
        """Resolve only rows actually owned by this type's kind of owner.

        Media of every owner shares one table and one PK sequence, so without this
        filter a product media PK encoded as `PageMedia` would resolve - under the
        wrong type, and behind the wrong permission.
        """
        return (
            models.ProductMedia.objects.filter(pk=id)
            .filter(**{f"{cls.owner_type}__isnull": False})
            .first()
        )

    @classmethod
    def resolve_url(
        cls,
        root: models.ProductMedia,
        info,
        *,
        size: int | None = None,
        format: str | None = None,
    ) -> str | None | Promise[str]:
        if root.external_url and root.type != ProductMediaTypes.IMAGE:
            return root.external_url

        # Bypass proxy URL when image is already in-place and original size is
        # requested.
        if root.image and size == 0:
            return build_absolute_uri(root.image.url)

        # If image is not there yet and original size is requested return proxy URL for
        # original.
        if size == 0:
            return build_absolute_uri(
                get_original_image_proxy_url(str(root.pk), cls.__name__)
            )

        # Else, return proxy URL for thumbnail.
        format = get_thumbnail_format(format)
        selected_size = get_thumbnail_size(size)

        def _resolve_url(thumbnail) -> str:
            url = get_image_or_proxy_url(
                thumbnail, str(root.pk), cls.__name__, selected_size, format
            )
            return build_absolute_uri(url)

        return (
            ThumbnailByProductMediaIdSizeAndFormatLoader(info.context)
            .load((root.pk, selected_size, format))
            .then(_resolve_url)
        )

    @staticmethod
    def resolve_media_type(root: models.ProductMedia, info) -> str:
        return root.type

    @staticmethod
    def resolve_owner_type(root: models.ProductMedia, info) -> str | None:
        return root.owner_type

    @staticmethod
    def resolve_owner_id(root: models.ProductMedia, info) -> str | None:
        owner_type = root.owner_type
        if not owner_type:
            return None
        return graphene.Node.to_global_id(
            OWNER_TYPE_TO_GRAPHQL_TYPE[owner_type], getattr(root, f"{owner_type}_id")
        )


@federated_entity("id")
class ProductMedia(MediaResolvers, ModelObjectType[models.ProductMedia]):
    id = graphene.GlobalID(
        required=True, description="The unique ID of the product media."
    )
    type = ProductMediaType(
        required=True,
        description="The type of the media.",
        deprecation_reason="Use the `mediaType` field instead.",
    )
    product_id = graphene.ID(description="Product id the media refers to.")

    class Meta:
        description = "Represents a product media."
        interfaces = [Media, relay.Node, ObjectWithMetadata]
        model = models.ProductMedia

    owner_type = MediaOwnerTypes.PRODUCT

    @staticmethod
    def __resolve_references(roots: list["ProductMedia"], info):
        database_connection_name = get_database_connection_name(info.context)
        return resolve_federation_references(
            ProductMedia,
            roots,
            models.ProductMedia.objects.using(database_connection_name).filter(
                product__isnull=False
            ),
        )

    @staticmethod
    def resolve_product_id(root: models.ProductMedia, info) -> str:
        return graphene.Node.to_global_id("Product", root.product_id)


class CategoryMedia(MediaResolvers, ModelObjectType[models.ProductMedia]):
    id = graphene.GlobalID(
        required=True, description="The unique ID of the category media."
    )

    class Meta:
        description = "Represents a category media." + ADDED_IN_324
        doc_category = DOC_CATEGORY_MEDIA
        interfaces = [Media, relay.Node, ObjectWithMetadata]
        model = models.ProductMedia

    owner_type = MediaOwnerTypes.CATEGORY


class CollectionMedia(MediaResolvers, ModelObjectType[models.ProductMedia]):
    id = graphene.GlobalID(
        required=True, description="The unique ID of the collection media."
    )

    class Meta:
        description = "Represents a collection media." + ADDED_IN_324
        doc_category = DOC_CATEGORY_MEDIA
        interfaces = [Media, relay.Node, ObjectWithMetadata]
        model = models.ProductMedia

    owner_type = MediaOwnerTypes.COLLECTION


class PageMedia(MediaResolvers, ModelObjectType[models.ProductMedia]):
    id = graphene.GlobalID(
        required=True, description="The unique ID of the page media."
    )

    class Meta:
        description = "Represents a page media." + ADDED_IN_324
        doc_category = DOC_CATEGORY_MEDIA
        interfaces = [Media, relay.Node, ObjectWithMetadata]
        model = models.ProductMedia

    owner_type = MediaOwnerTypes.PAGE


MEDIA_TYPE_BY_OWNER_TYPE = {
    MediaOwnerTypes.PRODUCT: ProductMedia,
    MediaOwnerTypes.CATEGORY: CategoryMedia,
    MediaOwnerTypes.COLLECTION: CollectionMedia,
    MediaOwnerTypes.PAGE: PageMedia,
}


def resolve_media_type_for_owner(media: models.ProductMedia):
    """Return the concrete GraphQL type matching the media's owner."""
    owner_type = media.owner_type
    return MEDIA_TYPE_BY_OWNER_TYPE[owner_type] if owner_type else None

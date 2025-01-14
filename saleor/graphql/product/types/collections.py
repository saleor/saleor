from collections import defaultdict

import graphene
from graphene import relay
from promise import Promise

from ....permission.enums import ProductPermissions
from ....product import models
from ....product.search import search_products
from ....thumbnail.utils import (
    get_image_or_proxy_url,
    get_thumbnail_format,
    get_thumbnail_size,
)
from ...channel import ChannelContext, ChannelQsContext
from ...channel.dataloaders import ChannelBySlugLoader
from ...channel.types import ChannelContextType, ChannelContextTypeWithMetadata
from ...core import ResolveInfo
from ...core.connection import (
    CountableConnection,
    create_connection_slice,
    filter_connection_queryset,
)
from ...core.context import get_database_connection_name
from ...core.descriptions import (
    DEPRECATED_IN_3X_FIELD,
    RICH_CONTENT,
)
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.federation import federated_entity
from ...core.fields import FilterConnectionField, JSONString, PermissionsField
from ...core.types import Image, NonNullList, ThumbnailField
from ...core.utils import from_global_id_or_error
from ...meta.types import ObjectWithMetadata
from ...translations.fields import TranslationField
from ...translations.types import CollectionTranslation
from ...utils import get_user_or_app_from_context
from ..dataloaders import (
    CollectionChannelListingByCollectionIdLoader,
    ThumbnailByCollectionIdSizeAndFormatLoader,
)
from ..filters import ProductFilterInput, ProductWhereInput
from ..sorters import ProductOrder
from ..utils import check_for_sorting_by_rank
from .channels import CollectionChannelListing
from .products import ProductCountableConnection


@federated_entity("id channel")
class Collection(ChannelContextTypeWithMetadata[models.Collection]):
    id = graphene.GlobalID(required=True, description="The ID of the collection.")
    seo_title = graphene.String(description="SEO title of the collection.")
    seo_description = graphene.String(description="SEO description of the collection.")
    name = graphene.String(required=True, description="Name of the collection.")
    description = JSONString(
        description="Description of the collection." + RICH_CONTENT
    )
    slug = graphene.String(required=True, description="Slug of the collection.")
    channel = graphene.String(
        description=(
            "Channel given to retrieve this collection. Also used by federation "
            "gateway to resolve this object in a federated query."
        ),
    )
    description_json = JSONString(
        description="Description of the collection." + RICH_CONTENT,
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use the `description` field instead."
        ),
    )
    products = FilterConnectionField(
        ProductCountableConnection,
        filter=ProductFilterInput(description="Filtering options for products."),
        where=ProductWhereInput(description="Filtering options for products."),
        sort_by=ProductOrder(description="Sort products."),
        description="List of products in this collection.",
    )
    background_image = ThumbnailField(description="Background image of the collection.")
    translation = TranslationField(
        CollectionTranslation,
        type_name="collection",
        resolver=ChannelContextType.resolve_translation,
    )
    channel_listings = PermissionsField(
        NonNullList(CollectionChannelListing),
        description="List of channels in which the collection is available.",
        permissions=[
            ProductPermissions.MANAGE_PRODUCTS,
        ],
    )

    class Meta:
        default_resolver = ChannelContextType.resolver_with_context
        description = "Represents a collection of products."
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.Collection

    @staticmethod
    def resolve_channel(root: ChannelContext[models.Product], _info):
        return root.channel_slug

    @staticmethod
    def resolve_background_image(
        root: ChannelContext[models.Collection],
        info: ResolveInfo,
        size: int | None = None,
        format: str | None = None,
    ) -> None | Image | Promise[Image]:
        node = root.node
        if not node.background_image:
            return None

        alt = node.background_image_alt
        if size == 0:
            return Image(url=node.background_image.url, alt=alt)

        format = get_thumbnail_format(format)
        selected_size = get_thumbnail_size(size)

        def _resolve_background_image(thumbnail):
            url = get_image_or_proxy_url(
                thumbnail, str(node.id), "Collection", selected_size, format
            )
            return Image(url=url, alt=alt)

        return (
            ThumbnailByCollectionIdSizeAndFormatLoader(info.context)
            .load((node.id, selected_size, format))
            .then(_resolve_background_image)
        )

    @staticmethod
    def resolve_products(
        root: ChannelContext[models.Collection], info: ResolveInfo, **kwargs
    ):
        check_for_sorting_by_rank(info, kwargs)
        search = kwargs.get("search")

        requestor = get_user_or_app_from_context(info.context)
        limited_channel_access = False if root.channel_slug is None else True

        def _resolve_products(channel):
            qs = root.node.products.using(
                get_database_connection_name(info.context)
            ).visible_to_user(requestor, channel, limited_channel_access)

            if search:
                qs = ChannelQsContext(
                    qs=search_products(qs.qs, search), channel_slug=root.channel_slug
                )
            else:
                qs = ChannelQsContext(qs=qs, channel_slug=root.channel_slug)

            kwargs["channel"] = root.channel_slug
            qs = filter_connection_queryset(
                qs, kwargs, allow_replica=info.context.allow_replica
            )
            return create_connection_slice(qs, info, kwargs, ProductCountableConnection)

        if root.channel_slug:
            return (
                ChannelBySlugLoader(info.context)
                .load(str(root.channel_slug))
                .then(_resolve_products)
            )
        return _resolve_products(None)

    @staticmethod
    def resolve_channel_listings(root: ChannelContext[models.Collection], info):
        return CollectionChannelListingByCollectionIdLoader(info.context).load(
            root.node.id
        )

    @staticmethod
    def resolve_description_json(root: ChannelContext[models.Collection], _info):
        description = root.node.description
        return description if description is not None else {}

    @staticmethod
    def __resolve_references(roots: list["Collection"], info: ResolveInfo):
        from ..resolvers import resolve_collections

        channels = defaultdict(set)
        roots_ids = []
        for root in roots:
            _, root_id = from_global_id_or_error(root.id, Collection, raise_error=True)
            roots_ids.append(f"{root.channel}_{root_id}")
            channels[root.channel].add(root_id)

        collections = {}
        for channel, ids in channels.items():
            queryset = resolve_collections(info, channel).qs.filter(id__in=ids)

            for collection in queryset:
                collections[f"{channel}_{collection.id}"] = ChannelContext(
                    channel_slug=channel, node=collection
                )

        return [collections.get(root_id) for root_id in roots_ids]


class CollectionCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        node = Collection
        description = "Represents a connection to a list of collections."

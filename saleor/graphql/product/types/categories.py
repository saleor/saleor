from typing import List, Optional

import graphene
from graphene import relay

from ....permission.utils import has_one_of_permissions
from ....product import models
from ....product.models import ALL_PRODUCTS_PERMISSIONS
from ....thumbnail.utils import (
    get_image_or_proxy_url,
    get_thumbnail_format,
    get_thumbnail_size,
)
from ...channel import ChannelQsContext
from ...channel.utils import get_default_channel_slug_or_graphql_error
from ...core.connection import (
    CountableConnection,
    create_connection_slice,
    filter_connection_queryset,
)
from ...core.descriptions import ADDED_IN_310, DEPRECATED_IN_3X_FIELD, RICH_CONTENT
from ...core.federation import federated_entity, resolve_federation_references
from ...core.fields import ConnectionField, FilterConnectionField, JSONString
from ...core.tracing import traced_resolver
from ...core.types import Image, ModelObjectType, ThumbnailField
from ...meta.types import ObjectWithMetadata
from ...translations.fields import TranslationField
from ...translations.types import CategoryTranslation
from ...utils import get_user_or_app_from_context
from ..dataloaders import (
    CategoryChildrenByCategoryIdLoader,
    ThumbnailByCategoryIdSizeAndFormatLoader,
)
from ..filters import ProductFilterInput
from ..sorters import ProductOrder
from .products import ProductCountableConnection


@federated_entity("id")
class Category(ModelObjectType[models.Category]):
    id = graphene.GlobalID(required=True)
    seo_title = graphene.String()
    seo_description = graphene.String()
    name = graphene.String(required=True)
    description = JSONString(description="Description of the category." + RICH_CONTENT)
    slug = graphene.String(required=True)
    parent = graphene.Field(lambda: Category)
    level = graphene.Int(required=True)
    description_json = JSONString(
        description="Description of the category." + RICH_CONTENT,
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use the `description` field instead."
        ),
    )
    ancestors = ConnectionField(
        lambda: CategoryCountableConnection,
        description="List of ancestors of the category.",
    )
    products = FilterConnectionField(
        ProductCountableConnection,
        filter=ProductFilterInput(
            description="Filtering options for products." + ADDED_IN_310
        ),
        sort_by=ProductOrder(description="Sort products." + ADDED_IN_310),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description=(
            "List of products in the category. Requires the following permissions to "
            "include the unpublished items: "
            f"{', '.join([p.name for p in ALL_PRODUCTS_PERMISSIONS])}."
        ),
    )
    children = ConnectionField(
        lambda: CategoryCountableConnection,
        description="List of children of the category.",
    )
    background_image = ThumbnailField()
    translation = TranslationField(CategoryTranslation, type_name="category")

    class Meta:
        description = (
            "Represents a single category of products. Categories allow to organize "
            "products in a tree-hierarchies which can be used for navigation in the "
            "storefront."
        )
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.Category

    @staticmethod
    def resolve_ancestors(root: models.Category, info, **kwargs):
        return create_connection_slice(
            root.get_ancestors(), info, kwargs, CategoryCountableConnection
        )

    @staticmethod
    def resolve_description_json(root: models.Category, _info):
        description = root.description
        return description if description is not None else {}

    @staticmethod
    def resolve_background_image(
        root: models.Category,
        info,
        size: Optional[int] = None,
        format: Optional[str] = None,
    ):
        if not root.background_image:
            return

        alt = root.background_image_alt
        if size == 0:
            return Image(url=root.background_image.url, alt=alt)

        format = get_thumbnail_format(format)
        selected_size = get_thumbnail_size(size)

        def _resolve_background_image(thumbnail):
            url = get_image_or_proxy_url(
                thumbnail, str(root.id), "Category", selected_size, format
            )
            return Image(url=url, alt=alt)

        return (
            ThumbnailByCategoryIdSizeAndFormatLoader(info.context)
            .load((root.id, selected_size, format))
            .then(_resolve_background_image)
        )

    @staticmethod
    def resolve_children(root: models.Category, info, **kwargs):
        def slice_children_categories(children):
            return create_connection_slice(
                children, info, kwargs, CategoryCountableConnection
            )

        return (
            CategoryChildrenByCategoryIdLoader(info.context)
            .load(root.pk)
            .then(slice_children_categories)
        )

    @staticmethod
    def resolve_url(root: models.Category, _info):
        return ""

    @staticmethod
    @traced_resolver
    def resolve_products(root: models.Category, info, *, channel=None, **kwargs):
        requestor = get_user_or_app_from_context(info.context)
        has_required_permissions = has_one_of_permissions(
            requestor, ALL_PRODUCTS_PERMISSIONS
        )
        tree = root.get_descendants(include_self=True)
        if channel is None and not has_required_permissions:
            channel = get_default_channel_slug_or_graphql_error()
        qs = models.Product.objects.all()
        if not has_required_permissions:
            qs = (
                qs.visible_to_user(requestor, channel)
                .annotate_visible_in_listings(channel)
                .exclude(
                    visible_in_listings=False,
                )
            )
        if channel and has_required_permissions:
            qs = qs.filter(channel_listings__channel__slug=channel)
        qs = qs.filter(category__in=tree)
        qs = ChannelQsContext(qs=qs, channel_slug=channel)

        kwargs["channel"] = channel
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, ProductCountableConnection)

    @staticmethod
    def __resolve_references(roots: List["Category"], _info):
        return resolve_federation_references(Category, roots, models.Category.objects)


class CategoryCountableConnection(CountableConnection):
    class Meta:
        node = Category

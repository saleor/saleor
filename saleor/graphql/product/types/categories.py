import graphene
from graphene import relay
from promise import Promise

from ....permission.utils import has_one_of_permissions
from ....product import models
from ....product.models import ALL_PRODUCTS_PERMISSIONS
from ....thumbnail.utils import (
    get_image_or_proxy_url,
    get_thumbnail_format,
    get_thumbnail_size,
)
from ...channel import ChannelQsContext
from ...channel.dataloaders import ChannelBySlugLoader
from ...channel.utils import get_default_channel_slug_or_graphql_error
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
from ...core.federation import federated_entity, resolve_federation_references
from ...core.fields import ConnectionField, FilterConnectionField, JSONString
from ...core.scalars import DateTime
from ...core.types import Image, ModelObjectType, ThumbnailField
from ...meta.types import ObjectWithMetadata
from ...translations.fields import TranslationField
from ...translations.types import CategoryTranslation
from ...utils import get_user_or_app_from_context
from ..dataloaders import (
    CategoryByIdLoader,
    CategoryChildrenByCategoryIdLoader,
    ThumbnailByCategoryIdSizeAndFormatLoader,
)
from ..filters import ProductFilterInput, ProductWhereInput
from ..sorters import ProductOrder
from .products import ProductCountableConnection


@federated_entity("id")
class Category(ModelObjectType[models.Category]):
    id = graphene.GlobalID(required=True, description="The ID of the category.")
    seo_title = graphene.String(description="SEO title of category.")
    seo_description = graphene.String(description="SEO description of category.")
    name = graphene.String(required=True, description="Name of category")
    description = JSONString(description="Description of the category." + RICH_CONTENT)
    slug = graphene.String(required=True, description="Slug of the category.")
    parent = graphene.Field(lambda: Category, description="Parent category.")
    level = graphene.Int(required=True, description="Level of the category.")
    description_json = JSONString(
        description="Description of the category." + RICH_CONTENT,
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use the `description` field instead."
        ),
    )
    updated_at = DateTime(
        required=True,
        description="The date and time when the category was last updated.",
    )
    ancestors = ConnectionField(
        lambda: CategoryCountableConnection,
        description="List of ancestors of the category.",
    )
    products = FilterConnectionField(
        ProductCountableConnection,
        filter=ProductFilterInput(description="Filtering options for products."),
        where=ProductWhereInput(description="Filtering options for products."),
        sort_by=ProductOrder(description="Sort products."),
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
    background_image = ThumbnailField(description="Background image of the category.")
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
        database_connection_name = get_database_connection_name(info.context)
        return create_connection_slice(
            root.get_ancestors().using(database_connection_name),
            info,
            kwargs,
            CategoryCountableConnection,
        )

    @staticmethod
    def resolve_description_json(root: models.Category, _info):
        description = root.description
        return description if description is not None else {}

    @staticmethod
    def resolve_background_image(
        root: models.Category,
        info,
        size: int | None = None,
        format: str | None = None,
    ) -> None | Image | Promise[Image]:
        if not root.background_image:
            return None

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
    def resolve_parent(root: models.Category, info):
        if root.parent_id:
            return CategoryByIdLoader(info.context).load(root.parent_id)
        return None

    @staticmethod
    def resolve_url(root: models.Category, _info):
        return ""

    @staticmethod
    def resolve_products(root: models.Category, info, *, channel=None, **kwargs):
        requestor = get_user_or_app_from_context(info.context)
        has_required_permissions = has_one_of_permissions(
            requestor, ALL_PRODUCTS_PERMISSIONS
        )
        tree = root.get_descendants(include_self=True)
        limited_channel_access = False if channel is None else True
        if channel is None and not has_required_permissions:
            channel = get_default_channel_slug_or_graphql_error(
                allow_replica=info.context.allow_replica
            )
        connection_name = get_database_connection_name(info.context)

        def _resolve_products(channel_obj):
            qs = models.Product.objects.using(connection_name).all()
            if not has_required_permissions:
                qs = (
                    qs.visible_to_user(requestor, channel_obj, limited_channel_access)
                    .annotate_visible_in_listings(channel_obj)
                    .exclude(
                        visible_in_listings=False,
                    )
                )
            if channel_obj and has_required_permissions:
                qs = qs.filter(channel_listings__channel_id=channel_obj.id)
            qs = qs.filter(category__in=tree)
            qs = ChannelQsContext(qs=qs, channel_slug=channel)

            kwargs["channel"] = channel
            qs = filter_connection_queryset(
                qs, kwargs, allow_replica=info.context.allow_replica
            )
            return create_connection_slice(qs, info, kwargs, ProductCountableConnection)

        if channel:
            return (
                ChannelBySlugLoader(info.context)
                .load(str(channel))
                .then(_resolve_products)
            )
        return _resolve_products(None)

    @staticmethod
    def __resolve_references(roots: list["Category"], info):
        database_connection_name = get_database_connection_name(info.context)
        return resolve_federation_references(
            Category, roots, models.Category.objects.using(database_connection_name)
        )


class CategoryCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        node = Category

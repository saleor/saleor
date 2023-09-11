import graphene

from ...permission.enums import ProductPermissions
from ...permission.utils import has_one_of_permissions
from ...product.models import ALL_PRODUCTS_PERMISSIONS
from ...product.search import search_products
from ..channel import ChannelContext, ChannelQsContext
from ..channel.utils import get_default_channel_slug_or_graphql_error
from ..core import ResolveInfo
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.descriptions import ADDED_IN_310, ADDED_IN_314, PREVIEW_FEATURE
from ..core.doc_category import DOC_CATEGORY_PRODUCTS
from ..core.enums import ReportingPeriod
from ..core.fields import (
    BaseField,
    ConnectionField,
    FilterConnectionField,
    PermissionsField,
)
from ..core.tracing import traced_resolver
from ..core.types import NonNullList
from ..core.utils import from_global_id_or_error
from ..core.validators import validate_one_of_args_is_in_query
from ..translations.mutations import (
    CategoryTranslate,
    CollectionTranslate,
    ProductBulkTranslate,
    ProductTranslate,
    ProductVariantBulkTranslate,
    ProductVariantTranslate,
)
from ..utils import get_user_or_app_from_context
from .bulk_mutations import (
    CategoryBulkDelete,
    CollectionBulkDelete,
    ProductBulkCreate,
    ProductBulkDelete,
    ProductMediaBulkDelete,
    ProductTypeBulkDelete,
    ProductVariantBulkCreate,
    ProductVariantBulkDelete,
    ProductVariantBulkUpdate,
    ProductVariantStocksCreate,
    ProductVariantStocksDelete,
    ProductVariantStocksUpdate,
)
from .dataloaders.products import CategoryByIdLoader, CategoryBySlugLoader
from .filters import (
    CategoryFilterInput,
    CategoryWhereInput,
    CollectionFilterInput,
    CollectionWhereInput,
    ProductFilterInput,
    ProductTypeFilterInput,
    ProductVariantFilterInput,
    ProductVariantWhereInput,
    ProductWhereInput,
)
from .mutations import (
    CategoryCreate,
    CategoryDelete,
    CategoryUpdate,
    CollectionAddProducts,
    CollectionCreate,
    CollectionDelete,
    CollectionRemoveProducts,
    CollectionReorderProducts,
    CollectionUpdate,
    ProductCreate,
    ProductDelete,
    ProductMediaCreate,
    ProductMediaDelete,
    ProductMediaReorder,
    ProductMediaUpdate,
    ProductTypeCreate,
    ProductTypeDelete,
    ProductTypeUpdate,
    ProductUpdate,
    ProductVariantCreate,
    ProductVariantDelete,
    ProductVariantPreorderDeactivate,
    ProductVariantReorder,
    ProductVariantSetDefault,
    ProductVariantUpdate,
    VariantMediaAssign,
    VariantMediaUnassign,
)
from .mutations.attributes import (
    ProductAttributeAssign,
    ProductAttributeAssignmentUpdate,
    ProductAttributeUnassign,
    ProductReorderAttributeValues,
    ProductTypeReorderAttributes,
    ProductVariantReorderAttributeValues,
)
from .mutations.channels import (
    CollectionChannelListingUpdate,
    ProductChannelListingUpdate,
    ProductVariantChannelListingUpdate,
)
from .mutations.digital_contents import (
    DigitalContentCreate,
    DigitalContentDelete,
    DigitalContentUpdate,
    DigitalContentUrlCreate,
)
from .resolvers import (
    resolve_categories,
    resolve_collection_by_id,
    resolve_collection_by_slug,
    resolve_collections,
    resolve_digital_content_by_id,
    resolve_digital_contents,
    resolve_product,
    resolve_product_type_by_id,
    resolve_product_types,
    resolve_product_variants,
    resolve_products,
    resolve_report_product_sales,
    resolve_variant,
)
from .sorters import (
    CategorySortingInput,
    CollectionSortingInput,
    ProductOrder,
    ProductTypeSortingInput,
    ProductVariantSortingInput,
)
from .types import (
    Category,
    CategoryCountableConnection,
    Collection,
    CollectionCountableConnection,
    DigitalContent,
    DigitalContentCountableConnection,
    Product,
    ProductCountableConnection,
    ProductType,
    ProductTypeCountableConnection,
    ProductVariant,
    ProductVariantCountableConnection,
)
from .utils import check_for_sorting_by_rank


class ProductQueries(graphene.ObjectType):
    digital_content = PermissionsField(
        DigitalContent,
        description="Look up digital content by ID.",
        id=graphene.Argument(
            graphene.ID, description="ID of the digital content.", required=True
        ),
        permissions=[
            ProductPermissions.MANAGE_PRODUCTS,
        ],
        doc_category=DOC_CATEGORY_PRODUCTS,
    )
    digital_contents = ConnectionField(
        DigitalContentCountableConnection,
        description="List of digital content.",
        permissions=[
            ProductPermissions.MANAGE_PRODUCTS,
        ],
        doc_category=DOC_CATEGORY_PRODUCTS,
    )
    categories = FilterConnectionField(
        CategoryCountableConnection,
        filter=CategoryFilterInput(description="Filtering options for categories."),
        where=CategoryWhereInput(
            description="Where filtering options." + ADDED_IN_314 + PREVIEW_FEATURE
        ),
        sort_by=CategorySortingInput(description="Sort categories."),
        level=graphene.Argument(
            graphene.Int,
            description="Filter categories by the nesting level in the category tree.",
        ),
        description="List of the shop's categories.",
        doc_category=DOC_CATEGORY_PRODUCTS,
    )
    category = BaseField(
        Category,
        id=graphene.Argument(graphene.ID, description="ID of the category."),
        slug=graphene.Argument(graphene.String, description="Slug of the category"),
        description="Look up a category by ID or slug.",
        doc_category=DOC_CATEGORY_PRODUCTS,
    )
    collection = BaseField(
        Collection,
        id=graphene.Argument(
            graphene.ID,
            description="ID of the collection.",
        ),
        slug=graphene.Argument(graphene.String, description="Slug of the category"),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description=(
            "Look up a collection by ID. Requires one of the following permissions to "
            "include the unpublished items: "
            f"{', '.join([p.name for p in ALL_PRODUCTS_PERMISSIONS])}."
        ),
        doc_category=DOC_CATEGORY_PRODUCTS,
    )
    collections = FilterConnectionField(
        CollectionCountableConnection,
        filter=CollectionFilterInput(description="Filtering options for collections."),
        where=CollectionWhereInput(
            description="Where filtering options." + ADDED_IN_314 + PREVIEW_FEATURE
        ),
        sort_by=CollectionSortingInput(description="Sort collections."),
        description=(
            "List of the shop's collections. Requires one of the following permissions "
            "to include the unpublished items: "
            f"{', '.join([p.name for p in ALL_PRODUCTS_PERMISSIONS])}."
        ),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        doc_category=DOC_CATEGORY_PRODUCTS,
    )
    product = BaseField(
        Product,
        id=graphene.Argument(
            graphene.ID,
            description="ID of the product.",
        ),
        slug=graphene.Argument(graphene.String, description="Slug of the product."),
        external_reference=graphene.Argument(
            graphene.String, description=f"External ID of the product. {ADDED_IN_310}"
        ),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description=(
            "Look up a product by ID. Requires one of the following permissions to "
            "include the unpublished items: "
            f"{', '.join([p.name for p in ALL_PRODUCTS_PERMISSIONS])}."
        ),
        doc_category=DOC_CATEGORY_PRODUCTS,
    )
    products = FilterConnectionField(
        ProductCountableConnection,
        filter=ProductFilterInput(description="Filtering options for products."),
        where=ProductWhereInput(
            description="Where filtering options." + ADDED_IN_314 + PREVIEW_FEATURE
        ),
        sort_by=ProductOrder(description="Sort products."),
        search=graphene.String(description="Search products." + ADDED_IN_314),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description=(
            "List of the shop's products. Requires one of the following permissions to "
            "include the unpublished items: "
            f"{', '.join([p.name for p in ALL_PRODUCTS_PERMISSIONS])}."
        ),
        doc_category=DOC_CATEGORY_PRODUCTS,
    )
    product_type = BaseField(
        ProductType,
        id=graphene.Argument(
            graphene.ID, description="ID of the product type.", required=True
        ),
        description="Look up a product type by ID.",
        doc_category=DOC_CATEGORY_PRODUCTS,
    )
    product_types = FilterConnectionField(
        ProductTypeCountableConnection,
        filter=ProductTypeFilterInput(
            description="Filtering options for product types."
        ),
        sort_by=ProductTypeSortingInput(description="Sort product types."),
        description="List of the shop's product types.",
        doc_category=DOC_CATEGORY_PRODUCTS,
    )
    product_variant = BaseField(
        ProductVariant,
        id=graphene.Argument(
            graphene.ID,
            description="ID of the product variant.",
        ),
        sku=graphene.Argument(
            graphene.String, description="SKU of the product variant."
        ),
        external_reference=graphene.Argument(
            graphene.String, description=f"External ID of the product. {ADDED_IN_310}"
        ),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description=(
            "Look up a product variant by ID or SKU. Requires one of the following "
            "permissions to include the unpublished items: "
            f"{', '.join([p.name for p in ALL_PRODUCTS_PERMISSIONS])}."
        ),
        doc_category=DOC_CATEGORY_PRODUCTS,
    )
    product_variants = FilterConnectionField(
        ProductVariantCountableConnection,
        ids=NonNullList(
            graphene.ID, description="Filter product variants by given IDs."
        ),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        filter=ProductVariantFilterInput(
            description="Filtering options for product variant."
        ),
        where=ProductVariantWhereInput(
            description="Where filtering options." + ADDED_IN_314 + PREVIEW_FEATURE
        ),
        sort_by=ProductVariantSortingInput(description="Sort products variants."),
        description=(
            "List of product variants. Requires one of the following permissions to "
            "include the unpublished items: "
            f"{', '.join([p.name for p in ALL_PRODUCTS_PERMISSIONS])}."
        ),
        doc_category=DOC_CATEGORY_PRODUCTS,
    )
    report_product_sales = ConnectionField(
        ProductVariantCountableConnection,
        period=graphene.Argument(
            ReportingPeriod, required=True, description="Span of time."
        ),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned.",
            required=True,
        ),
        description="List of top selling products.",
        permissions=[
            ProductPermissions.MANAGE_PRODUCTS,
        ],
        doc_category=DOC_CATEGORY_PRODUCTS,
    )

    @staticmethod
    def resolve_categories(_root, info: ResolveInfo, *, level=None, **kwargs):
        qs = resolve_categories(info, level=level)
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, CategoryCountableConnection)

    @staticmethod
    def resolve_category(_root, info: ResolveInfo, *, id=None, slug=None, **kwargs):
        validate_one_of_args_is_in_query("id", id, "slug", slug)
        if id:
            _, id = from_global_id_or_error(id, Category)
            # FIXME: we should raise an error above
            if id is not None:
                return CategoryByIdLoader(info.context).load(int(id))
            return None
        if slug:
            return CategoryBySlugLoader(info.context).load(slug)

    @staticmethod
    @traced_resolver
    def resolve_collection(
        _root, info: ResolveInfo, *, id=None, slug=None, channel=None
    ):
        validate_one_of_args_is_in_query("id", id, "slug", slug)
        requestor = get_user_or_app_from_context(info.context)

        has_required_permissions = has_one_of_permissions(
            requestor, ALL_PRODUCTS_PERMISSIONS
        )
        if channel is None and not has_required_permissions:
            channel = get_default_channel_slug_or_graphql_error()
        if id:
            _, id = from_global_id_or_error(id, Collection)
            collection = resolve_collection_by_id(info, id, channel, requestor)
        else:
            collection = resolve_collection_by_slug(
                info, slug=slug, channel_slug=channel, requestor=requestor
            )
        return (
            ChannelContext(node=collection, channel_slug=channel)
            if collection
            else None
        )

    @staticmethod
    def resolve_collections(_root, info: ResolveInfo, *, channel=None, **kwargs):
        requestor = get_user_or_app_from_context(info.context)
        has_required_permissions = has_one_of_permissions(
            requestor, ALL_PRODUCTS_PERMISSIONS
        )
        if channel is None and not has_required_permissions:
            channel = get_default_channel_slug_or_graphql_error()
        qs = resolve_collections(info, channel)
        kwargs["channel"] = channel
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, CollectionCountableConnection)

    @staticmethod
    def resolve_digital_content(_root, _info: ResolveInfo, *, id):
        _, id = from_global_id_or_error(id, DigitalContent)
        return resolve_digital_content_by_id(id)

    @staticmethod
    def resolve_digital_contents(_root, info: ResolveInfo, **kwargs):
        qs = resolve_digital_contents(info)
        return create_connection_slice(
            qs, info, kwargs, DigitalContentCountableConnection
        )

    @staticmethod
    @traced_resolver
    def resolve_product(
        _root,
        info: ResolveInfo,
        *,
        id=None,
        slug=None,
        external_reference=None,
        channel=None,
    ):
        validate_one_of_args_is_in_query(
            "id", id, "slug", slug, "external_reference", external_reference
        )
        requestor = get_user_or_app_from_context(info.context)

        has_required_permissions = has_one_of_permissions(
            requestor, ALL_PRODUCTS_PERMISSIONS
        )

        if channel is None and not has_required_permissions:
            channel = get_default_channel_slug_or_graphql_error()

        product = resolve_product(
            info,
            id=id,
            slug=slug,
            external_reference=external_reference,
            channel_slug=channel,
            requestor=requestor,
        )

        return ChannelContext(node=product, channel_slug=channel) if product else None

    @staticmethod
    @traced_resolver
    def resolve_products(_root, info: ResolveInfo, *, channel=None, **kwargs):
        check_for_sorting_by_rank(info, kwargs)
        search = kwargs.get("search")

        requestor = get_user_or_app_from_context(info.context)
        has_required_permissions = has_one_of_permissions(
            requestor, ALL_PRODUCTS_PERMISSIONS
        )
        if channel is None and not has_required_permissions:
            channel = get_default_channel_slug_or_graphql_error()
        qs = resolve_products(info, requestor, channel_slug=channel)
        if search:
            qs = ChannelQsContext(
                qs=search_products(qs.qs, search), channel_slug=channel
            )
        kwargs["channel"] = channel
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, ProductCountableConnection)

    @staticmethod
    def resolve_product_type(_root, _info: ResolveInfo, *, id):
        _, id = from_global_id_or_error(id, ProductType)
        return resolve_product_type_by_id(id)

    @staticmethod
    def resolve_product_types(_root, info: ResolveInfo, **kwargs):
        qs = resolve_product_types(info)
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, ProductTypeCountableConnection)

    @staticmethod
    @traced_resolver
    def resolve_product_variant(
        _root,
        info: ResolveInfo,
        *,
        id=None,
        sku=None,
        external_reference=None,
        channel=None,
    ):
        validate_one_of_args_is_in_query(
            "id", id, "sku", sku, "external_reference", external_reference
        )
        requestor = get_user_or_app_from_context(info.context)
        has_required_permissions = has_one_of_permissions(
            requestor, ALL_PRODUCTS_PERMISSIONS
        )

        if channel is None and not has_required_permissions:
            channel = get_default_channel_slug_or_graphql_error()

        variant = resolve_variant(
            info,
            id,
            sku,
            external_reference,
            channel_slug=channel,
            requestor=requestor,
            requestor_has_access_to_all=has_required_permissions,
        )

        return ChannelContext(node=variant, channel_slug=channel) if variant else None

    @staticmethod
    def resolve_product_variants(
        _root, info: ResolveInfo, *, ids=None, channel=None, **kwargs
    ):
        requestor = get_user_or_app_from_context(info.context)
        has_required_permissions = has_one_of_permissions(
            requestor, ALL_PRODUCTS_PERMISSIONS
        )
        if channel is None and not has_required_permissions:
            channel = get_default_channel_slug_or_graphql_error()
        qs = resolve_product_variants(
            info,
            ids=ids,
            channel_slug=channel,
            requestor_has_access_to_all=has_required_permissions,
            requestor=requestor,
        )
        kwargs["channel"] = qs.channel_slug
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(
            qs, info, kwargs, ProductVariantCountableConnection
        )

    @staticmethod
    @traced_resolver
    def resolve_report_product_sales(
        _root, info: ResolveInfo, *, period, channel, **kwargs
    ):
        qs = resolve_report_product_sales(period, channel_slug=channel)
        kwargs["channel"] = qs.channel_slug
        return create_connection_slice(
            qs, info, kwargs, ProductVariantCountableConnection
        )


class ProductMutations(graphene.ObjectType):
    product_attribute_assign = ProductAttributeAssign.Field()
    product_attribute_assignment_update = ProductAttributeAssignmentUpdate.Field()
    product_attribute_unassign = ProductAttributeUnassign.Field()

    category_create = CategoryCreate.Field()
    category_delete = CategoryDelete.Field()
    category_bulk_delete = CategoryBulkDelete.Field()
    category_update = CategoryUpdate.Field()
    category_translate = CategoryTranslate.Field()

    collection_add_products = CollectionAddProducts.Field()
    collection_create = CollectionCreate.Field()
    collection_delete = CollectionDelete.Field()
    collection_reorder_products = CollectionReorderProducts.Field()
    collection_bulk_delete = CollectionBulkDelete.Field()
    collection_remove_products = CollectionRemoveProducts.Field()
    collection_update = CollectionUpdate.Field()
    collection_translate = CollectionTranslate.Field()
    collection_channel_listing_update = CollectionChannelListingUpdate.Field()

    product_create = ProductCreate.Field()
    product_delete = ProductDelete.Field()
    product_bulk_create = ProductBulkCreate.Field()
    product_bulk_delete = ProductBulkDelete.Field()
    product_update = ProductUpdate.Field()
    product_bulk_translate = ProductBulkTranslate.Field()
    product_translate = ProductTranslate.Field()

    product_channel_listing_update = ProductChannelListingUpdate.Field()

    product_media_create = ProductMediaCreate.Field()
    product_variant_reorder = ProductVariantReorder.Field()
    product_media_delete = ProductMediaDelete.Field()
    product_media_bulk_delete = ProductMediaBulkDelete.Field()
    product_media_reorder = ProductMediaReorder.Field()
    product_media_update = ProductMediaUpdate.Field()

    product_type_create = ProductTypeCreate.Field()
    product_type_delete = ProductTypeDelete.Field()
    product_type_bulk_delete = ProductTypeBulkDelete.Field()
    product_type_update = ProductTypeUpdate.Field()
    product_type_reorder_attributes = ProductTypeReorderAttributes.Field()
    product_reorder_attribute_values = ProductReorderAttributeValues.Field()

    digital_content_create = DigitalContentCreate.Field()
    digital_content_delete = DigitalContentDelete.Field()
    digital_content_update = DigitalContentUpdate.Field()

    digital_content_url_create = DigitalContentUrlCreate.Field()

    product_variant_create = ProductVariantCreate.Field()
    product_variant_delete = ProductVariantDelete.Field()
    product_variant_bulk_create = ProductVariantBulkCreate.Field()
    product_variant_bulk_update = ProductVariantBulkUpdate.Field()
    product_variant_bulk_delete = ProductVariantBulkDelete.Field()
    product_variant_stocks_create = ProductVariantStocksCreate.Field()
    product_variant_stocks_delete = ProductVariantStocksDelete.Field()
    product_variant_stocks_update = ProductVariantStocksUpdate.Field()
    product_variant_update = ProductVariantUpdate.Field()
    product_variant_set_default = ProductVariantSetDefault.Field()
    product_variant_translate = ProductVariantTranslate.Field()
    product_variant_bulk_translate = ProductVariantBulkTranslate.Field()
    product_variant_channel_listing_update = ProductVariantChannelListingUpdate.Field()
    product_variant_reorder_attribute_values = (
        ProductVariantReorderAttributeValues.Field()
    )
    product_variant_preorder_deactivate = ProductVariantPreorderDeactivate.Field()

    variant_media_assign = VariantMediaAssign.Field()
    variant_media_unassign = VariantMediaUnassign.Field()

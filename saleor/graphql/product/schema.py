import graphene

from ...account.utils import requestor_is_staff_member_or_app
from ...core.permissions import ProductPermissions
from ..channel import ChannelContext
from ..channel.utils import get_default_channel_slug_or_graphql_error
from ..core.enums import ReportingPeriod
from ..core.fields import (
    ChannelContextFilterConnectionField,
    FilterInputConnectionField,
    PrefetchingConnectionField,
)
from ..core.validators import validate_one_of_args_is_in_query
from ..decorators import permission_required
from ..translations.mutations import (
    CategoryTranslate,
    CollectionTranslate,
    ProductTranslate,
    ProductVariantTranslate,
)
from ..utils import get_user_or_app_from_context
from .bulk_mutations.products import (
    CategoryBulkDelete,
    CollectionBulkDelete,
    ProductBulkDelete,
    ProductImageBulkDelete,
    ProductTypeBulkDelete,
    ProductVariantBulkCreate,
    ProductVariantBulkDelete,
    ProductVariantStocksCreate,
    ProductVariantStocksDelete,
    ProductVariantStocksUpdate,
)
from .enums import StockAvailability
from .filters import (
    CategoryFilterInput,
    CollectionFilterInput,
    ProductFilterInput,
    ProductTypeFilterInput,
    ProductVariantFilterInput,
)
from .mutations.attributes import (
    ProductAttributeAssign,
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
from .mutations.products import (
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
    ProductImageCreate,
    ProductImageDelete,
    ProductImageReorder,
    ProductImageUpdate,
    ProductTypeCreate,
    ProductTypeDelete,
    ProductTypeUpdate,
    ProductUpdate,
    ProductVariantCreate,
    ProductVariantDelete,
    ProductVariantReorder,
    ProductVariantSetDefault,
    ProductVariantUpdate,
    VariantImageAssign,
    VariantImageUnassign,
)
from .resolvers import (
    resolve_categories,
    resolve_category_by_slug,
    resolve_collection_by_id,
    resolve_collection_by_slug,
    resolve_collections,
    resolve_digital_contents,
    resolve_product_by_id,
    resolve_product_by_slug,
    resolve_product_types,
    resolve_product_variant_by_sku,
    resolve_product_variants,
    resolve_products,
    resolve_report_product_sales,
    resolve_variant_by_id,
)
from .sorters import (
    CategorySortingInput,
    CollectionSortingInput,
    ProductOrder,
    ProductTypeSortingInput,
)
from .types import (
    Category,
    Collection,
    DigitalContent,
    Product,
    ProductType,
    ProductVariant,
)


class ProductQueries(graphene.ObjectType):
    digital_content = graphene.Field(
        DigitalContent,
        description="Look up digital content by ID.",
        id=graphene.Argument(
            graphene.ID, description="ID of the digital content.", required=True
        ),
    )
    digital_contents = PrefetchingConnectionField(
        DigitalContent, description="List of digital content."
    )
    categories = FilterInputConnectionField(
        Category,
        filter=CategoryFilterInput(description="Filtering options for categories."),
        sort_by=CategorySortingInput(description="Sort categories."),
        level=graphene.Argument(
            graphene.Int,
            description="Filter categories by the nesting level in the category tree.",
        ),
        description="List of the shop's categories.",
    )
    category = graphene.Field(
        Category,
        id=graphene.Argument(graphene.ID, description="ID of the category."),
        slug=graphene.Argument(graphene.String, description="Slug of the category"),
        description="Look up a category by ID or slug.",
    )
    collection = graphene.Field(
        Collection,
        id=graphene.Argument(
            graphene.ID,
            description="ID of the collection.",
        ),
        slug=graphene.Argument(graphene.String, description="Slug of the category"),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="Look up a collection by ID.",
    )
    collections = ChannelContextFilterConnectionField(
        Collection,
        filter=CollectionFilterInput(description="Filtering options for collections."),
        sort_by=CollectionSortingInput(description="Sort collections."),
        description="List of the shop's collections.",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
    )
    product = graphene.Field(
        Product,
        id=graphene.Argument(
            graphene.ID,
            description="ID of the product.",
        ),
        slug=graphene.Argument(graphene.String, description="Slug of the product."),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="Look up a product by ID.",
    )
    products = ChannelContextFilterConnectionField(
        Product,
        filter=ProductFilterInput(description="Filtering options for products."),
        sort_by=ProductOrder(description="Sort products."),
        stock_availability=graphene.Argument(
            StockAvailability,
            description=(
                "[Deprecated] Filter products by stock availability. Use the `filter` "
                "field instead. This field will be removed after 2020-07-31."
            ),
        ),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="List of the shop's products.",
    )
    product_type = graphene.Field(
        ProductType,
        id=graphene.Argument(
            graphene.ID, description="ID of the product type.", required=True
        ),
        description="Look up a product type by ID.",
    )
    product_types = FilterInputConnectionField(
        ProductType,
        filter=ProductTypeFilterInput(
            description="Filtering options for product types."
        ),
        sort_by=ProductTypeSortingInput(description="Sort product types."),
        description="List of the shop's product types.",
    )
    product_variant = graphene.Field(
        ProductVariant,
        id=graphene.Argument(
            graphene.ID,
            description="ID of the product variant.",
        ),
        sku=graphene.Argument(
            graphene.String, description="Sku of the product variant."
        ),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="Look up a product variant by ID or SKU.",
    )
    product_variants = ChannelContextFilterConnectionField(
        ProductVariant,
        ids=graphene.List(
            graphene.ID, description="Filter product variants by given IDs."
        ),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        filter=ProductVariantFilterInput(
            description="Filtering options for product variant."
        ),
        description="List of product variants.",
    )
    report_product_sales = ChannelContextFilterConnectionField(
        ProductVariant,
        period=graphene.Argument(
            ReportingPeriod, required=True, description="Span of time."
        ),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned.",
            required=True,
        ),
        description="List of top selling products.",
    )

    def resolve_categories(self, info, level=None, **kwargs):
        return resolve_categories(info, level=level, **kwargs)

    def resolve_category(self, info, id=None, slug=None, **kwargs):
        validate_one_of_args_is_in_query("id", id, "slug", slug)
        if id:
            return graphene.Node.get_node_from_global_id(info, id, Category)
        if slug:
            return resolve_category_by_slug(slug=slug)

    def resolve_collection(self, info, id=None, slug=None, channel=None, **_kwargs):
        validate_one_of_args_is_in_query("id", id, "slug", slug)
        requestor = get_user_or_app_from_context(info.context)

        is_staff = requestor_is_staff_member_or_app(requestor)
        if channel is None and not is_staff:
            channel = get_default_channel_slug_or_graphql_error()
        if id:
            _, id = graphene.Node.from_global_id(id)
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

    def resolve_collections(self, info, channel=None, *_args, **_kwargs):
        requestor = get_user_or_app_from_context(info.context)
        is_staff = requestor_is_staff_member_or_app(requestor)
        if channel is None and not is_staff:
            channel = get_default_channel_slug_or_graphql_error()
        return resolve_collections(info, channel)

    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_digital_content(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, DigitalContent)

    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_digital_contents(self, info, **_kwargs):
        return resolve_digital_contents(info)

    def resolve_product(self, info, id=None, slug=None, channel=None, **_kwargs):
        validate_one_of_args_is_in_query("id", id, "slug", slug)
        requestor = get_user_or_app_from_context(info.context)
        is_staff = requestor_is_staff_member_or_app(requestor)

        if channel is None and not is_staff:
            channel = get_default_channel_slug_or_graphql_error()
        if id:
            _, id = graphene.Node.from_global_id(id)
            product = resolve_product_by_id(
                info, id, channel_slug=channel, requestor=requestor
            )
        else:
            product = resolve_product_by_slug(
                info, product_slug=slug, channel_slug=channel, requestor=requestor
            )
        return ChannelContext(node=product, channel_slug=channel) if product else None

    def resolve_products(self, info, channel=None, **kwargs):
        requestor = get_user_or_app_from_context(info.context)
        if channel is None and not requestor_is_staff_member_or_app(requestor):
            channel = get_default_channel_slug_or_graphql_error()
        return resolve_products(info, requestor, channel_slug=channel, **kwargs)

    def resolve_product_type(self, info, id, **_kwargs):
        return graphene.Node.get_node_from_global_id(info, id, ProductType)

    def resolve_product_types(self, info, **kwargs):
        return resolve_product_types(info, **kwargs)

    def resolve_product_variant(
        self,
        info,
        id=None,
        sku=None,
        channel=None,
    ):
        validate_one_of_args_is_in_query("id", id, "sku", sku)
        requestor = get_user_or_app_from_context(info.context)
        is_staff = requestor_is_staff_member_or_app(requestor)
        if channel is None and not is_staff:
            channel = get_default_channel_slug_or_graphql_error()
        if id:
            _, id = graphene.Node.from_global_id(id)
            variant = resolve_variant_by_id(
                info, id, channel_slug=channel, requestor=requestor
            )
        else:
            variant = resolve_product_variant_by_sku(
                info,
                sku=sku,
                channel_slug=channel,
                requestor=requestor,
                requestor_has_access_to_all=is_staff,
            )
        return ChannelContext(node=variant, channel_slug=channel) if variant else None

    def resolve_product_variants(self, info, ids=None, channel=None, **_kwargs):
        requestor = get_user_or_app_from_context(info.context)
        is_staff = requestor_is_staff_member_or_app(requestor)
        if channel is None and not is_staff:
            channel = get_default_channel_slug_or_graphql_error()
        return resolve_product_variants(
            info,
            ids=ids,
            channel_slug=channel,
            requestor_has_access_to_all=is_staff,
            requestor=requestor,
        )

    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_report_product_sales(self, *_args, period, channel, **_kwargs):
        return resolve_report_product_sales(period, channel_slug=channel)


class ProductMutations(graphene.ObjectType):
    product_attribute_assign = ProductAttributeAssign.Field()
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
    product_bulk_delete = ProductBulkDelete.Field()
    product_update = ProductUpdate.Field()
    product_translate = ProductTranslate.Field()

    product_channel_listing_update = ProductChannelListingUpdate.Field()

    product_image_create = ProductImageCreate.Field()
    product_variant_reorder = ProductVariantReorder.Field()
    product_image_delete = ProductImageDelete.Field()
    product_image_bulk_delete = ProductImageBulkDelete.Field()
    product_image_reorder = ProductImageReorder.Field()
    product_image_update = ProductImageUpdate.Field()

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
    product_variant_bulk_delete = ProductVariantBulkDelete.Field()
    product_variant_stocks_create = ProductVariantStocksCreate.Field()
    product_variant_stocks_delete = ProductVariantStocksDelete.Field()
    product_variant_stocks_update = ProductVariantStocksUpdate.Field()
    product_variant_update = ProductVariantUpdate.Field()
    product_variant_set_default = ProductVariantSetDefault.Field()
    product_variant_translate = ProductVariantTranslate.Field()
    product_variant_channel_listing_update = ProductVariantChannelListingUpdate.Field()
    product_variant_reorder_attribute_values = (
        ProductVariantReorderAttributeValues.Field()
    )

    variant_image_assign = VariantImageAssign.Field()
    variant_image_unassign = VariantImageUnassign.Field()

import graphene
from graphql_jwt.decorators import permission_required

from ..core.enums import ReportingPeriod
from ..core.fields import (
    FilterInputConnectionField, PrefetchingConnectionField)
from ..core.types import FilterInputObjectType
from ..descriptions import DESCRIPTIONS
from ..translations.mutations import (
    AttributeTranslate, AttributeValueTranslate, CategoryTranslate,
    CollectionTranslate, ProductTranslate, ProductVariantTranslate)
from .bulk_mutations.attributes import (
    AttributeBulkDelete, AttributeValueBulkDelete)
from .bulk_mutations.products import (
    CategoryBulkDelete, CollectionBulkDelete, CollectionBulkPublish,
    ProductBulkDelete, ProductBulkPublish, ProductImageBulkDelete,
    ProductTypeBulkDelete, ProductVariantBulkDelete)
from .enums import StockAvailability
from .filters import CollectionFilter, ProductFilter, ProductTypeFilter
from .mutations.attributes import (
    AttributeCreate, AttributeDelete, AttributeUpdate, AttributeValueCreate,
    AttributeValueDelete, AttributeValueUpdate)
from .mutations.digital_contents import (
    DigitalContentCreate, DigitalContentDelete, DigitalContentUpdate,
    DigitalContentUrlCreate)
from .mutations.products import (
    CategoryCreate, CategoryDelete, CategoryUpdate, CollectionAddProducts,
    CollectionCreate, CollectionDelete, CollectionRemoveProducts,
    CollectionUpdate, ProductCreate, ProductDelete, ProductImageCreate,
    ProductImageDelete, ProductImageReorder, ProductImageUpdate,
    ProductTypeCreate, ProductTypeDelete, ProductTypeUpdate, ProductUpdate,
    ProductVariantCreate, ProductVariantDelete, ProductVariantUpdate,
    VariantImageAssign, VariantImageUnassign)
from .resolvers import (
    resolve_attributes, resolve_categories, resolve_collections,
    resolve_digital_contents, resolve_product_types, resolve_product_variants,
    resolve_products, resolve_report_product_sales)
from .scalars import AttributeScalar
from .types import (
    Attribute, Category, Collection, DigitalContent, Product, ProductOrder,
    ProductType, ProductVariant)


class ProductFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = ProductFilter


class CollectionFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = CollectionFilter


class ProductTypeFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = ProductTypeFilter


class ProductQueries(graphene.ObjectType):
    digital_content = graphene.Field(
        DigitalContent, id=graphene.Argument(graphene.ID, required=True))
    digital_contents = PrefetchingConnectionField(
        DigitalContent, query=graphene.String(),
        level=graphene.Argument(graphene.Int),
        description='List of the digital contents.')
    attributes = PrefetchingConnectionField(
        Attribute,
        description='List of the shop\'s attributes.',
        query=graphene.String(description=DESCRIPTIONS['attributes']),
        in_category=graphene.Argument(
            graphene.ID, description='''Return attributes for products 
            belonging to the given category.'''),
        in_collection=graphene.Argument(
            graphene.ID, description='''Return attributes for products
            belonging to the given collection.'''), )
    categories = PrefetchingConnectionField(
        Category, query=graphene.String(
            description=DESCRIPTIONS['category']),
        level=graphene.Argument(graphene.Int),
        description='List of the shop\'s categories.')
    category = graphene.Field(
        Category, id=graphene.Argument(graphene.ID, required=True),
        description='Lookup a category by ID.')
    collection = graphene.Field(
        Collection, id=graphene.Argument(graphene.ID, required=True),
        description='Lookup a collection by ID.')
    collections = FilterInputConnectionField(
        Collection, filter=CollectionFilterInput(), query=graphene.String(
            description=DESCRIPTIONS['collection']),
        description='List of the shop\'s collections.')
    product = graphene.Field(
        Product, id=graphene.Argument(graphene.ID, required=True),
        description='Lookup a product by ID.')
    products = FilterInputConnectionField(
        Product,
        filter=ProductFilterInput(),
        attributes=graphene.List(
            AttributeScalar, description='Filter products by attributes.'),
        categories=graphene.List(
            graphene.ID, description='Filter products by category.'),
        collections=graphene.List(
            graphene.ID, description='Filter products by collections.'),
        price_lte=graphene.Float(
            description='Filter by price less than or equal to the given value.'),
        price_gte=graphene.Float(
            description='Filter by price greater than or equal to the given value.'),
        sort_by=graphene.Argument(
            ProductOrder, description='Sort products.'),
        stock_availability=graphene.Argument(
            StockAvailability,
            description='Filter products by the stock availability'),
        query=graphene.String(description=DESCRIPTIONS['product']),
        description='List of the shop\'s products.')
    product_type = graphene.Field(
        ProductType, id=graphene.Argument(graphene.ID, required=True),
        description='Lookup a product type by ID.')
    product_types = FilterInputConnectionField(
        ProductType, filter=ProductTypeFilterInput(),
        description='List of the shop\'s product types.')
    product_variant = graphene.Field(
        ProductVariant, id=graphene.Argument(graphene.ID, required=True),
        description='Lookup a variant by ID.')
    product_variants = PrefetchingConnectionField(
        ProductVariant, ids=graphene.List(graphene.ID),
        description='Lookup multiple variants by ID')
    report_product_sales = PrefetchingConnectionField(
        ProductVariant,
        period=graphene.Argument(
            ReportingPeriod, required=True, description='Span of time.'),
        description='List of top selling products.')

    def resolve_attributes(
            self, info, in_category=None, in_collection=None, query=None,
            **_kwargs):
        return resolve_attributes(info, in_category, in_collection, query)

    def resolve_categories(self, info, level=None, query=None, **_kwargs):
        return resolve_categories(info, level=level, query=query)

    def resolve_category(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, Category)

    def resolve_collection(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, Collection)

    def resolve_collections(self, info, query=None, **_kwargs):
        return resolve_collections(info, query)

    @permission_required('product.manage_products')
    def resolve_digital_content(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, DigitalContent)

    @permission_required('product.manage_products')
    def resolve_digital_contents(self, info, **_kwargs):
        return resolve_digital_contents(info)

    def resolve_product(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, Product)

    def resolve_products(self, info, **kwargs):
        return resolve_products(info, **kwargs)

    def resolve_product_type(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, ProductType)

    def resolve_product_types(self, info, **_kwargs):
        return resolve_product_types(info)

    def resolve_product_variant(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, ProductVariant)

    def resolve_product_variants(self, info, ids=None, **_kwargs):
        return resolve_product_variants(info, ids)

    @permission_required(['order.manage_orders', 'product.manage_products'])
    def resolve_report_product_sales(self, *_args, period, **_kwargs):
        return resolve_report_product_sales(period)


class ProductMutations(graphene.ObjectType):
    attribute_create = AttributeCreate.Field()
    attribute_delete = AttributeDelete.Field()
    attribute_bulk_delete = AttributeBulkDelete.Field()
    attribute_update = AttributeUpdate.Field()
    attribute_translate = AttributeTranslate.Field()

    attribute_value_create = AttributeValueCreate.Field()
    attribute_value_delete = AttributeValueDelete.Field()
    attribute_value_bulk_delete = AttributeValueBulkDelete.Field()
    attribute_value_update = AttributeValueUpdate.Field()
    attribute_value_translate = AttributeValueTranslate.Field()

    category_create = CategoryCreate.Field()
    category_delete = CategoryDelete.Field()
    category_bulk_delete = CategoryBulkDelete.Field()
    category_update = CategoryUpdate.Field()
    category_translate = CategoryTranslate.Field()

    collection_add_products = CollectionAddProducts.Field()
    collection_create = CollectionCreate.Field()
    collection_delete = CollectionDelete.Field()
    collection_bulk_delete = CollectionBulkDelete.Field()
    collection_bulk_publish = CollectionBulkPublish.Field()
    collection_remove_products = CollectionRemoveProducts.Field()
    collection_update = CollectionUpdate.Field()
    collection_translate = CollectionTranslate.Field()

    product_create = ProductCreate.Field()
    product_delete = ProductDelete.Field()
    product_bulk_delete = ProductBulkDelete.Field()
    product_bulk_publish = ProductBulkPublish.Field()
    product_update = ProductUpdate.Field()
    product_translate = ProductTranslate.Field()

    product_image_create = ProductImageCreate.Field()
    product_image_delete = ProductImageDelete.Field()
    product_image_bulk_delete = ProductImageBulkDelete.Field()
    product_image_reorder = ProductImageReorder.Field()
    product_image_update = ProductImageUpdate.Field()

    product_type_create = ProductTypeCreate.Field()
    product_type_delete = ProductTypeDelete.Field()
    product_type_bulk_delete = ProductTypeBulkDelete.Field()
    product_type_update = ProductTypeUpdate.Field()

    digital_content_create = DigitalContentCreate.Field()
    digital_content_delete = DigitalContentDelete.Field()
    digital_content_update = DigitalContentUpdate.Field()

    digital_content_url_create = DigitalContentUrlCreate.Field()

    product_variant_create = ProductVariantCreate.Field()
    product_variant_delete = ProductVariantDelete.Field()
    product_variant_bulk_delete = ProductVariantBulkDelete.Field()
    product_variant_update = ProductVariantUpdate.Field()
    product_variant_translate = ProductVariantTranslate.Field()

    variant_image_assign = VariantImageAssign.Field()
    variant_image_unassign = VariantImageUnassign.Field()

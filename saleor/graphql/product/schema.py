import graphene
from graphene_django.filter import DjangoFilterConnectionField
from graphql_jwt.decorators import staff_member_required

from ..descriptions import DESCRIPTIONS
from .filters import ProductFilterSet
from .mutations.attributes import (
    AttributeValueCreate, AttributeValueDelete,
    AttributeValueUpdate, AttributeCreate, AttributeDelete,
    AttributeUpdate)
from .mutations.products import (
    CategoryCreate, CategoryDelete, CategoryUpdate,
    CollectionAddProducts, CollectionCreate, CollectionDelete,
    CollectionRemoveProducts, CollectionUpdate, ProductCreate,
    ProductDelete, ProductUpdate, ProductTypeCreate,
    ProductTypeDelete, ProductImageCreate, ProductImageDelete,
    ProductImageReorder, ProductImageUpdate, ProductTypeUpdate,
    ProductVariantCreate, ProductVariantDelete,
    ProductVariantUpdate, VariantImageAssign, VariantImageUnassign)
from .resolvers import (
    resolve_attributes, resolve_categories, resolve_collections,
    resolve_products, resolve_product_types, resolve_product_variants,
    resolve_report_product_sales)
from .types import (
    ReportingPeriod, Category, Collection, Product, Attribute, ProductType,
    ProductVariant, StockAvailability)


class ProductQueries(graphene.ObjectType):
    attributes = DjangoFilterConnectionField(
        Attribute,
        query=graphene.String(description=DESCRIPTIONS['attributes']),
        in_category=graphene.Argument(graphene.ID),
        description='List of the shop\'s attributes.')
    categories = DjangoFilterConnectionField(
        Category, query=graphene.String(
            description=DESCRIPTIONS['category']),
        level=graphene.Argument(graphene.Int),
        description='List of the shop\'s categories.')
    category = graphene.Field(
        Category, id=graphene.Argument(graphene.ID),
        description='Lookup a category by ID.')
    collection = graphene.Field(
        Collection, id=graphene.Argument(graphene.ID),
        description='Lookup a collection by ID.')
    collections = DjangoFilterConnectionField(
        Collection, query=graphene.String(
            description=DESCRIPTIONS['collection']),
        description='List of the shop\'s collections.')
    product = graphene.Field(
        Product, id=graphene.Argument(graphene.ID),
        description='Lookup a product by ID.')
    products = DjangoFilterConnectionField(
        Product, filterset_class=ProductFilterSet,
        query=graphene.String(description=DESCRIPTIONS['product']),
        stock_availability=graphene.Argument(
            StockAvailability,
            description='Filter products by the stock availability'),
        description='List of the shop\'s products.')
    product_type = graphene.Field(
        ProductType, id=graphene.Argument(graphene.ID),
        description='Lookup a product type by ID.')
    product_types = DjangoFilterConnectionField(
        ProductType, description='List of the shop\'s product types.')
    product_variant = graphene.Field(
        ProductVariant, id=graphene.Argument(graphene.ID),
        description='Lookup a variant by ID.')
    product_variants = DjangoFilterConnectionField(
        ProductVariant, ids=graphene.List(graphene.ID),
        description='Lookup multiple variants by ID')
    report_product_sales = DjangoFilterConnectionField(
        ProductVariant,
        period=graphene.Argument(ReportingPeriod, required=True),
        description='List of top selling products.')

    def resolve_attributes(self, info, in_category=None, query=None, **kwargs):
        return resolve_attributes(info, in_category, query)

    def resolve_category(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, Category)

    def resolve_categories(self, info, level=None, query=None, **kwargs):
        return resolve_categories(info, level=level, query=query)

    def resolve_collection(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, Collection)

    def resolve_collections(self, info, query=None, **kwargs):
        return resolve_collections(info, query)

    def resolve_product(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, Product)

    def resolve_products(
            self, info, category_id=None, stock_availability=None, query=None,
            **kwargs):
        return resolve_products(info, category_id, stock_availability, query)

    def resolve_product_type(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, ProductType)

    def resolve_product_types(self, info, **kwargs):
        return resolve_product_types()

    def resolve_product_variant(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, ProductVariant)

    def resolve_product_variants(self, info, ids=None, **kwargs):
        return resolve_product_variants(info, ids)

    @staff_member_required
    def resolve_report_product_sales(self, info, period, **kwargs):
        return resolve_report_product_sales(info, period)


class ProductMutations(graphene.ObjectType):
    attribute_create = AttributeCreate.Field()
    attribute_delete = AttributeDelete.Field()
    attribute_update = AttributeUpdate.Field()

    attribute_value_create = AttributeValueCreate.Field()
    attribute_value_delete = AttributeValueDelete.Field()
    attribute_value_update = AttributeValueUpdate.Field()

    category_create = CategoryCreate.Field()
    category_delete = CategoryDelete.Field()
    category_update = CategoryUpdate.Field()

    collection_create = CollectionCreate.Field()
    collection_update = CollectionUpdate.Field()
    collection_delete = CollectionDelete.Field()
    collection_add_products = CollectionAddProducts.Field()
    collection_remove_products = CollectionRemoveProducts.Field()

    product_create = ProductCreate.Field()
    product_delete = ProductDelete.Field()
    product_update = ProductUpdate.Field()

    product_image_create = ProductImageCreate.Field()
    product_image_reorder = ProductImageReorder.Field()
    product_image_delete = ProductImageDelete.Field()
    product_image_update = ProductImageUpdate.Field()

    product_type_create = ProductTypeCreate.Field()
    product_type_update = ProductTypeUpdate.Field()
    product_type_delete = ProductTypeDelete.Field()

    product_variant_create = ProductVariantCreate.Field()
    product_variant_delete = ProductVariantDelete.Field()
    product_variant_update = ProductVariantUpdate.Field()

    variant_image_assign = VariantImageAssign.Field()
    variant_image_unassign = VariantImageUnassign.Field()

import graphene
import graphql_jwt
from graphene_django.fields import DjangoConnectionField
from graphene_django.filter import DjangoFilterConnectionField
from graphql_jwt.decorators import permission_required

from .account.mutations import (
    CustomerCreate, CustomerUpdate, SetPassword, StaffCreate, StaffUpdate)
from .account.resolvers import (
    resolve_customer, resolve_customers, resolve_groups, resolve_staff_user,
    resolve_staff_users)
from .account.types import Group, User
from .descriptions import DESCRIPTIONS
from .discount.resolvers import resolve_sales, resolve_vouchers
from .discount.types import Sale, Voucher
from .core.filters import DistinctFilterSet
from .core.mutations import CreateToken, VerifyToken
from .core.resolvers import resolve_shop
from .core.types import Shop
from .order.filters import OrderFilter
from .order.resolvers import resolve_order, resolve_orders
from .order.types import Order
from .page.resolvers import resolve_pages, resolve_page
from .page.types import Page
from .page.mutations import PageCreate, PageDelete, PageUpdate
from .product.filters import ProductFilterSet
from .product.mutations import (
    CategoryCreateMutation, CategoryDelete, CategoryUpdateMutation,
    CollectionAddProducts, CollectionCreateMutation, CollectionDelete,
    CollectionRemoveProducts, CollectionUpdate, ProductCreateMutation,
    ProductDeleteMutation, ProductUpdateMutation, ProductTypeCreateMutation,
    ProductTypeDeleteMutation, ProductImageCreateMutation,
    ProductTypeUpdateMutation, ProductVariantCreateMutation,
    ProductVariantDeleteMutation, ProductVariantUpdateMutation)
from .product.resolvers import (
    resolve_attributes, resolve_categories, resolve_collections,
    resolve_products, resolve_product_types)
from .product.types import (
    Category, Collection, Product, ProductAttribute, ProductType)
from .shipping.resolvers import resolve_shipping_methods
from .shipping.types import ShippingMethod
from .utils import get_node


class Query(graphene.ObjectType):
    attributes = DjangoFilterConnectionField(
        ProductAttribute, filterset_class=DistinctFilterSet,
        query=graphene.String(description=DESCRIPTIONS['attributes']),
        in_category=graphene.Argument(graphene.ID),
        description='List of the shop\'s product attributes.')
    categories = DjangoFilterConnectionField(
        Category, filterset_class=DistinctFilterSet, query=graphene.String(
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
    customer = graphene.Field(
        User, id=graphene.Argument(graphene.ID),
        description='Lookup a customer by ID.')
    customers = DjangoFilterConnectionField(
        User, description='List of the shop\'s customers.',
        query=graphene.String(
            description=DESCRIPTIONS['customer']))
    groups = DjangoConnectionField(
        Group, query=graphene.String(description=DESCRIPTIONS['group']),
        description='List of shop\'s permission groups.')
    order = graphene.Field(
        Order, description='Lookup an order by ID.',
        id=graphene.Argument(graphene.ID))
    orders = DjangoFilterConnectionField(
        Order, filterset_class=OrderFilter, query=graphene.String(
            description=DESCRIPTIONS['order']),
        description='List of the shop\'s orders.')
    page = graphene.Field(
        Page, id=graphene.Argument(graphene.ID), slug=graphene.String(
            description=DESCRIPTIONS['page']),
        description='Lookup a page by ID or by slug.')
    pages = DjangoFilterConnectionField(
        Page, filterset_class=DistinctFilterSet, query=graphene.String(),
        description='List of the shop\'s pages.')
    product = graphene.Field(
        Product, id=graphene.Argument(graphene.ID),
        description='Lookup a product by ID.')
    products = DjangoFilterConnectionField(
        Product, filterset_class=ProductFilterSet, query=graphene.String(
            description=DESCRIPTIONS['product']),
        description='List of the shop\'s products.')
    product_type = graphene.Field(
        ProductType, id=graphene.Argument(graphene.ID),
        description='Lookup a product type by ID.')
    product_types = DjangoFilterConnectionField(
        ProductType, filterset_class=DistinctFilterSet,
        description='List of the shop\'s product types.')
    sale = graphene.Field(
        Sale, id=graphene.Argument(graphene.ID),
        description='Lookup a sale by ID.')
    sales = DjangoFilterConnectionField(
        Sale, query=graphene.String(description=DESCRIPTIONS['sale']),
        description="List of the shop\'s sales.")
    shop = graphene.Field(
        Shop, description='Represents a shop resources.',
        resolver=resolve_shop)
    staff_user = graphene.Field(
        User, id=graphene.Argument(graphene.ID),
        description='Lookup a staff user by ID.')
    staff_users = DjangoFilterConnectionField(
        User, description='List of the shop\'s staff users.',
        query=graphene.String(
            description=DESCRIPTIONS['staff']))
    voucher = graphene.Field(
        Voucher, id=graphene.Argument(graphene.ID),
        description='Lookup a voucher by ID.')
    vouchers = DjangoFilterConnectionField(
        Voucher, query=graphene.String(description=DESCRIPTIONS['product']),
        description="List of the shop\'s vouchers.")
    shipping_method = graphene.Field(
        ShippingMethod, id=graphene.Argument(graphene.ID),
        description='Lookup a shipping method by ID.')
    shipping_methods = DjangoFilterConnectionField(
        ShippingMethod, description='List of the shop\'s shipping methods.')
    node = graphene.Node.Field()

    def resolve_attributes(self, info, in_category=None, query=None, **kwargs):
        return resolve_attributes(in_category, info, query)

    def resolve_category(self, info, id):
        return get_node(info, id, only_type=Category)

    def resolve_categories(self, info, level=None, query=None, **kwargs):
        return resolve_categories(info, level=level, query=query)

    def resolve_collection(self, info, id):
        return get_node(info, id, only_type=Collection)

    def resolve_collections(self, info, query=None, **kwargs):
        resolve_collections(info, query)

    def resolve_customer(self, info, id):
        return resolve_customer(info, id)

    def resolve_customers(self, info, query=None, **kwargs):
        return resolve_customers(info, query=query)

    def resolve_groups(self, info, query=None, **kwargs):
        return resolve_groups(info, query)

    def resolve_page(self, info, id=None, slug=None):
        return resolve_page(info, id, slug)

    def resolve_pages(self, info, query=None, **kwargs):
        return resolve_pages(user=info.context.user, query=query)

    def resolve_order(self, info, id):
        return resolve_order(info, id)

    def resolve_orders(self, info, query=None, **kwargs):
        return resolve_orders(info, query)

    def resolve_product(self, info, id):
        return get_node(info, id, only_type=Product)

    def resolve_products(self, info, category_id=None, query=None, **kwargs):
        return resolve_products(info, category_id, query)

    def resolve_product_type(self, info, id):
        return get_node(info, id, only_type=ProductType)

    def resolve_product_types(self, info):
        return resolve_product_types()

    @permission_required('discount.view_sale')
    def resolve_sale(self, info, id):
        return get_node(info, id, only_type=Sale)

    @permission_required('discount.view_sale')
    def resolve_sales(self, info, query=None, **kwargs):
        return resolve_sales(info, query)

    @permission_required('discount.view_voucher')
    def resolve_voucher(self, info, id):
        return get_node(info, id, only_type=Voucher)

    @permission_required('discount.view_voucher')
    def resolve_vouchers(self, info, query=None, **kwargs):
        return resolve_vouchers(info, query)

    def resolve_shipping_method(self, info, id):
        return get_node(info, id, only_type=ShippingMethod)

    def resolve_shipping_methods(self, info, **kwargs):
        return resolve_shipping_methods(info)

    def resolve_staff_user(self, info, id):
        return resolve_staff_user(info, id)

    def resolve_staff_users(self, info, query=None, **kwargs):
        return resolve_staff_users(info, query=query)


class Mutations(graphene.ObjectType):
    token_create = CreateToken.Field()
    token_refresh = graphql_jwt.Refresh.Field()
    token_verify = VerifyToken.Field()

    set_password = SetPassword.Field()

    category_create = CategoryCreateMutation.Field()
    category_delete = CategoryDelete.Field()
    category_update = CategoryUpdateMutation.Field()

    customer_create = CustomerCreate.Field()
    customer_update = CustomerUpdate.Field()

    staff_create = StaffCreate.Field()
    staff_update = StaffUpdate.Field()

    collection_create = CollectionCreateMutation.Field()
    collection_update = CollectionUpdate.Field()
    collection_delete = CollectionDelete.Field()
    collection_add_products = CollectionAddProducts.Field()
    collection_remove_products = CollectionRemoveProducts.Field()

    page_create = PageCreate.Field()
    page_delete = PageDelete.Field()
    page_update = PageUpdate.Field()

    product_create = ProductCreateMutation.Field()
    product_delete = ProductDeleteMutation.Field()
    product_update = ProductUpdateMutation.Field()

    product_image_create = ProductImageCreateMutation.Field()

    product_type_create = ProductTypeCreateMutation.Field()
    product_type_update = ProductTypeUpdateMutation.Field()
    product_type_delete = ProductTypeDeleteMutation.Field()

    product_variant_create = ProductVariantCreateMutation.Field()
    product_variant_delete = ProductVariantDeleteMutation.Field()
    product_variant_update = ProductVariantUpdateMutation.Field()


schema = graphene.Schema(Query, Mutations)

import graphene
from django.core.exceptions import ValidationError

from .....discount.error_codes import DiscountErrorCode
from .....permission.enums import DiscountPermissions
from .....product.utils import get_products_ids_without_variants
from .....webhook.event_types import WebhookEventAsyncType
from ....channel import ChannelContext
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_31
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.mutations import BaseMutation
from ....core.types import BaseInputObjectType, DiscountError, NonNullList
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ....product.types import Category, Collection, Product, ProductVariant
from ...types import Voucher


class CatalogueInput(BaseInputObjectType):
    products = NonNullList(
        graphene.ID, description="Products related to the discount.", name="products"
    )
    categories = NonNullList(
        graphene.ID,
        description="Categories related to the discount.",
        name="categories",
    )
    collections = NonNullList(
        graphene.ID,
        description="Collections related to the discount.",
        name="collections",
    )
    variants = NonNullList(
        graphene.ID,
        description="Product variant related to the discount." + ADDED_IN_31,
        name="variants",
    )

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS


class VoucherBaseCatalogueMutation(BaseMutation):
    voucher = graphene.Field(
        Voucher, description="Voucher of which catalogue IDs will be modified."
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of a voucher.")
        input = CatalogueInput(
            required=True,
            description="Fields required to modify catalogue IDs of voucher.",
        )

    class Meta:
        abstract = True

    @classmethod
    def mutate(cls, root, info: ResolveInfo, **data):
        response = super().mutate(root, info, **data)
        if response.voucher:
            response.voucher = ChannelContext(node=response.voucher, channel_slug=None)
        return response

    @classmethod
    def clean_product(cls, products):
        products_ids_without_variants = get_products_ids_without_variants(products)
        if products_ids_without_variants:
            error_code = DiscountErrorCode.CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT.value
            raise ValidationError(
                {
                    "products": ValidationError(
                        "Cannot manage products without variants.",
                        code=error_code,
                        params={"products": products_ids_without_variants},
                    )
                }
            )


class VoucherAddCatalogues(VoucherBaseCatalogueMutation):
    class Meta:
        description = "Adds products, categories, collections to a voucher."
        doc_category = DOC_CATEGORY_DISCOUNTS
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.VOUCHER_UPDATED,
                description="A voucher was updated.",
            )
        ]

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        voucher = cls.get_node_or_error(
            info, data.get("id"), only_type=Voucher, field="voucher_id"
        )
        if voucher:
            input_data = data.get("input", {})
            cls.add_catalogues_to_node(voucher, input_data)

            if input_data:
                manager = get_plugin_manager_promise(info.context).get()
                cls.call_event(manager.voucher_updated, voucher, voucher.code)

        return VoucherAddCatalogues(voucher=voucher)

    @classmethod
    def add_catalogues_to_node(cls, node, input):
        products = input.get("products", [])
        if products:
            products = cls.get_nodes_or_error(products, "products", Product)
            cls.clean_product(products)
            node.products.add(*products)
        categories = input.get("categories", [])
        if categories:
            categories = cls.get_nodes_or_error(categories, "categories", Category)
            node.categories.add(*categories)
        collections = input.get("collections", [])
        if collections:
            collections = cls.get_nodes_or_error(collections, "collections", Collection)
            node.collections.add(*collections)
        variants = input.get("variants", [])
        if variants:
            variants = cls.get_nodes_or_error(variants, "variants", ProductVariant)
            node.variants.add(*variants)

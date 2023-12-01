from .....permission.enums import DiscountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.types import DiscountError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ....product.types import Category, Collection, Product, ProductVariant
from ...types import Voucher
from .voucher_add_catalogues import VoucherBaseCatalogueMutation


class VoucherRemoveCatalogues(VoucherBaseCatalogueMutation):
    class Meta:
        description = "Removes products, categories, collections from a voucher."
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
            cls.remove_catalogues_from_node(voucher, input_data)

            if input_data:
                manager = get_plugin_manager_promise(info.context).get()
                cls.call_event(manager.voucher_updated, voucher, voucher.code)

        return VoucherRemoveCatalogues(voucher=voucher)

    @classmethod
    def remove_catalogues_from_node(cls, node, input):
        products = input.get("products", [])
        if products:
            products = cls.get_nodes_or_error(products, "products", Product)
            node.products.remove(*products)
        categories = input.get("categories", [])
        if categories:
            categories = cls.get_nodes_or_error(categories, "categories", Category)
            node.categories.remove(*categories)
        collections = input.get("collections", [])
        if collections:
            collections = cls.get_nodes_or_error(collections, "collections", Collection)
            node.collections.remove(*collections)
        variants = input.get("variants", [])
        if variants:
            variants = cls.get_nodes_or_error(variants, "variants", ProductVariant)
            node.variants.remove(*variants)
        # Updated the db entries, recalculating discounts of affected products

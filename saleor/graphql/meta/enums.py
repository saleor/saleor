from ...attribute.models import Attribute
from ...core.models import ModelWithExternalReference
from ...discount.models import Promotion, Voucher
from ...order.models import Order
from ...product.models import Category, Collection, Product, ProductVariant
from ...warehouse.models import Warehouse
from ..core.descriptions import ADDED_IN_323
from ..core.types import BaseEnum


class ExternalReferenceTypeEnum(BaseEnum):
    ATTRIBUTE = "Attribute"
    CATEGORY = "Category"
    COLLECTION = "Collection"
    ORDER = "Order"
    PRODUCT = "Product"
    PRODUCT_VARIANT = "ProductVariant"
    PROMOTION = "Promotion"
    VOUCHER = "Voucher"
    WAREHOUSE = "Warehouse"

    class Meta:
        description = (
            "Type of an object that can be looked up by its external reference."
            + ADDED_IN_323
        )


EXTERNAL_REFERENCE_TYPE_TO_MODEL: dict[str, type[ModelWithExternalReference]] = {
    model.__name__: model
    for model in (
        Attribute,
        Category,
        Collection,
        Order,
        Product,
        ProductVariant,
        Promotion,
        Voucher,
        Warehouse,
    )
}

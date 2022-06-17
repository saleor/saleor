from dataclasses import dataclass
from decimal import Decimal

from typing import List, Optional

from .models import Voucher


@dataclass
class VoucherInfo:
    """It contains the voucher's details and PKs of all applicable objects."""

    voucher: Voucher
    product_pks: List[int]
    variant_pks: List[int]
    collection_pks: List[int]
    category_pks: List[int]


@dataclass
class DiscountData:
    """It contains all data related to discount."""
    name: str
    value_type: str
    value: Decimal
    active: bool
    translated_name: Optional[str]
    code: Optional[str]
    reason: Optional[str]


def fetch_voucher_info(voucher: Voucher) -> VoucherInfo:
    variant_pks = list(variant.id for variant in voucher.variants.all())
    product_pks = list(product.id for product in voucher.products.all())
    category_pks = list(category.id for category in voucher.categories.all())
    collection_pks = list(collection.id for collection in voucher.collections.all())

    return VoucherInfo(
        voucher=voucher,
        product_pks=product_pks,
        variant_pks=variant_pks,
        collection_pks=collection_pks,
        category_pks=category_pks,
    )



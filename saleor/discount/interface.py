from dataclasses import dataclass
from typing import List

from .models import Voucher


@dataclass
class VoucherInfo:
    """It contains the voucher's details and PKs of all applicable objects."""

    voucher: Voucher
    product_pks: List[int]
    variant_pks: List[int]
    collection_pks: List[int]
    category_pks: List[int]


def fetch_voucher_info(voucher: Voucher) -> VoucherInfo:
    product_pks = list(
        Voucher.products.through.objects.filter(voucher_id=voucher.id).values_list(
            "product_id", flat=True
        )
    )
    variant_pks = list(
        Voucher.variants.through.objects.filter(voucher_id=voucher.id).values_list(
            "productvariant_id", flat=True
        )
    )
    collection_pks = list(
        Voucher.collections.through.objects.filter(voucher_id=voucher.id).values_list(
            "collection_id", flat=True
        )
    )
    category_pks = list(
        Voucher.categories.through.objects.filter(voucher_id=voucher.id).values_list(
            "category_id", flat=True
        )
    )

    return VoucherInfo(
        voucher=voucher,
        product_pks=product_pks,
        variant_pks=variant_pks,
        collection_pks=collection_pks,
        category_pks=category_pks,
    )

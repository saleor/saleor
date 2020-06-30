from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, List

from promise import Promise

from ...checkout.models import CheckoutLine
from ..core.dataloaders import DataLoader
from ..product.dataloaders import (
    CollectionsByVariantIdLoader,
    ProductByVariantIdLoader,
    ProductVariantByIdLoader,
)

if TYPE_CHECKING:
    from ...product.models import Collection, Product, ProductVariant


@dataclass
class CheckoutLineInfo:
    line: "CheckoutLine"
    variant: "ProductVariant"
    product: "Product"
    collections: List["Collection"]


class CheckoutLinesInfoByCheckoutTokenLoader(DataLoader):
    context_key = "checkoutlinesinfo_by_checkout"

    def batch_load(self, keys):
        def with_checkout_lines(checkout_lines):
            variants_pks = list(
                {line.variant_id for lines in checkout_lines for line in lines}
            )

            def with_variants_products_collections(results):
                variants, products, collections = results
                variants_map = dict(zip(variants_pks, variants))
                products_map = dict(zip(variants_pks, products))
                collections_map = dict(zip(variants_pks, collections))

                lines_info = []
                for lines in checkout_lines:
                    lines_info.append(
                        [
                            CheckoutLineInfo(
                                line=line,
                                variant=variants_map[line.variant_id],
                                product=products_map[line.variant_id],
                                collections=collections_map[line.variant_id],
                            )
                            for line in lines
                        ]
                    )
                return lines_info

            variants = ProductVariantByIdLoader(self.context).load_many(variants_pks)
            products = ProductByVariantIdLoader(self.context).load_many(variants_pks)
            collections = CollectionsByVariantIdLoader(self.context).load_many(
                variants_pks
            )
            return Promise.all([variants, products, collections]).then(
                with_variants_products_collections
            )

        return (
            CheckoutLinesByCheckoutTokenLoader(self.context)
            .load_many(keys)
            .then(with_checkout_lines)
        )


class CheckoutLinesByCheckoutTokenLoader(DataLoader):
    context_key = "checkoutlines_by_checkout"

    def batch_load(self, keys):
        lines = CheckoutLine.objects.filter(checkout_id__in=keys)
        line_map = defaultdict(list)
        for line in lines.iterator():
            line_map[line.checkout_id].append(line)
        return [line_map.get(checkout_id, []) for checkout_id in keys]

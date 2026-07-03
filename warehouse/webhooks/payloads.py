from collections.abc import Iterable
from typing import TYPE_CHECKING, Optional

import graphene

from ...core.db.connection import allow_writer
from ...webhook import traced_payload_generator
from ...webhook.payload_helpers import generate_meta, generate_requestor
from ...webhook.payload_serializers import PayloadSerializer

if TYPE_CHECKING:
    from ...plugins.base_plugin import RequestorOrLazyObject
    from ..models import Stock


@allow_writer()
@traced_payload_generator
def generate_product_variant_with_stock_payload(
    stocks: Iterable["Stock"], requestor: Optional["RequestorOrLazyObject"] = None
):
    serializer = PayloadSerializer()
    extra_dict_data = {
        "product_id": lambda v: graphene.Node.to_global_id(
            "Product", v.product_variant.product_id
        ),
        "product_variant_id": lambda v: graphene.Node.to_global_id(
            "ProductVariant", v.product_variant_id
        ),
        "warehouse_id": lambda v: graphene.Node.to_global_id(
            "Warehouse", v.warehouse_id
        ),
        "product_slug": lambda v: v.product_variant.product.slug,
        "meta": generate_meta(requestor_data=generate_requestor(requestor)),
    }
    return serializer.serialize(stocks, fields=[], extra_dict_data=extra_dict_data)

from typing import Any, Dict, Optional

import graphene
from django.contrib.auth.models import AnonymousUser
from django.db.models import F
from django.utils import timezone

from saleor import __version__
from saleor.account.models import User
from saleor.core.prices import quantize_price
from saleor.order.models import Fulfillment, FulfillmentLine, OrderLine
from saleor.plugins.base_plugin import RequestorOrLazyObject
from saleor.warehouse.models import Warehouse
from saleor.webhook import traced_payload_generator
from saleor.webhook.payload_serializers import PayloadSerializer

ADDRESS_FIELDS = (
    "first_name",
    "last_name",
    "company_name",
    "street_address_1",
    "street_address_2",
    "city",
    "city_area",
    "postal_code",
    "country",
    "country_area",
    "phone",
)


def generate_requestor(requestor: Optional["RequestorOrLazyObject"] = None):
    if not requestor:
        return {"id": None, "type": None}
    if isinstance(requestor, (User, AnonymousUser)):
        return {"id": graphene.Node.to_global_id("User", requestor.id), "type": "user"}
    return {"id": requestor.name, "type": "app"}  # type: ignore


def generate_meta(*, requestor_data: Dict[str, Any], **kwargs):
    meta_result = {
        "issued_at": timezone.now().isoformat(),
        "version": __version__,
        "issuing_principal": requestor_data,
    }

    meta_result.update(kwargs)

    return meta_result


def generate_collection_point_payload(warehouse: "Warehouse"):
    serializer = PayloadSerializer()
    collection_point_fields = (
        "name",
        "email",
        "click_and_collect_option",
        "is_private",
    )
    collection_point_data = serializer.serialize(
        [warehouse],
        fields=collection_point_fields,
        additional_fields={"address": (lambda w: w.address, ADDRESS_FIELDS)},
    )
    return collection_point_data


@traced_payload_generator
def generate_fulfillment_lines_payload(fulfillment: Fulfillment):
    serializer = PayloadSerializer()
    lines = FulfillmentLine.objects.prefetch_related(
        "order_line__variant__product__product_type", "stock"
    ).filter(fulfillment=fulfillment)
    line_fields = ("quantity",)
    return serializer.serialize(
        lines,
        fields=line_fields,
        extra_dict_data={
            "product_name": lambda fl: fl.order_line.product_name,
            "variant_name": lambda fl: fl.order_line.variant_name,
            "product_sku": lambda fl: fl.order_line.product_sku,
            "product_variant_id": lambda fl: fl.order_line.product_variant_id,
            "weight": (
                lambda fl: fl.order_line.variant.get_weight().g
                if fl.order_line.variant
                else None
            ),
            "weight_unit": "gram",
            "product_type": (
                lambda fl: fl.order_line.variant.product.product_type.name
                if fl.order_line.variant
                else None
            ),
            "unit_price_net": lambda fl: quantize_price(
                fl.order_line.unit_price_net_amount, fl.order_line.currency
            ),
            "unit_price_gross": lambda fl: quantize_price(
                fl.order_line.unit_price_gross_amount, fl.order_line.currency
            ),
            "undiscounted_unit_price_net": (
                lambda fl: quantize_price(
                    fl.order_line.undiscounted_unit_price.net.amount,
                    fl.order_line.currency,
                )
            ),
            "undiscounted_unit_price_gross": (
                lambda fl: quantize_price(
                    fl.order_line.undiscounted_unit_price.gross.amount,
                    fl.order_line.currency,
                )
            ),
            "total_price_net_amount": (
                lambda fl: quantize_price(
                    fl.order_line.undiscounted_unit_price.net.amount,
                    fl.order_line.currency,
                )
                * fl.quantity
            ),
            "total_price_gross_amount": (
                lambda fl: quantize_price(
                    fl.order_line.undiscounted_unit_price.gross.amount,
                    fl.order_line.currency,
                )
                * fl.quantity
            ),
            "currency": lambda fl: fl.order_line.currency,
            "warehouse_id": lambda fl: graphene.Node.to_global_id(
                "Warehouse", fl.stock.warehouse_id
            )
            if fl.stock
            else None,
            "sale_id": lambda fl: fl.order_line.sale_id,
            "voucher_code": lambda fl: fl.order_line.voucher_code,
        },
    )


def prepare_order_lines_allocations_payload(line):
    warehouse_id_quantity_allocated_map = list(
        line.allocations.values(  # type: ignore
            "quantity_allocated",
            warehouse_id=F("stock__warehouse_id"),
        )
    )
    for item in warehouse_id_quantity_allocated_map:
        item["warehouse_id"] = graphene.Node.to_global_id(
            "Warehouse", item["warehouse_id"]
        )
    return warehouse_id_quantity_allocated_map


def charge_taxes(order_line: OrderLine) -> Optional[bool]:
    variant = order_line.variant
    return None if not variant else variant.product.charge_taxes


def get_product_metadata_for_order_line(line: OrderLine) -> Optional[dict]:
    variant = line.variant
    if not variant:
        return None
    return variant.product.metadata


def get_product_type_metadata_for_order_line(line: OrderLine) -> Optional[dict]:
    variant = line.variant
    if not variant:
        return None
    return variant.product.product_type.metadata

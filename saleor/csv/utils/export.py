from collections import ChainMap
from typing import TYPE_CHECKING, Dict, List, Set, Tuple, Union

import petl as etl
from django.db.models import F

if TYPE_CHECKING:
    # flake8: noqa
    from ..product.models import Product, ProductVariant


def export_products(queryset, delimiter=";"):
    file_name = "product_data.csv"
    headers_mapping = {
        "product": {
            "id": "id",
            "name": "name",
            "description": "description",
            "product_type__name": "product type",
            "category__slug": "category",
            "is_published": "visible",
            "price_amount": "price",
            "product_currency": "product currency",
        },
        "variant": {
            "sku": "sku",
            "price_override_amount": "price override",
            "cost_price_amount": "cost price",
            "variant_currency": "variant_currency",
        },
        "common": {"images": "images"},
    }

    products_attributes_fields = set()
    variants_attributes_fields = set()
    warehouse_fields = set()

    products_with_variants_data = []
    products_data = queryset.annotate(product_currency=F("currency")).values(
        *headers_mapping["product"].keys()
    )

    for product, product_data in zip(queryset, products_data):
        product_data, attributes_fields = update_product_data(product, product_data)
        products_attributes_fields.update(attributes_fields)
        products_with_variants_data.append(product_data)

        variants = product.variants.all()
        variants_data = variants.annotate(variant_currency=F("currency")).values(
            *headers_mapping["variant"].keys()
        )
        for variant, variant_data in zip(variants, variants_data):
            variant_data, attribute_data, warehouse_data = create_variant_data(
                variant, variant_data
            )
            variants_attributes_fields.update(attribute_data)
            warehouse_fields.update(warehouse_data)
            products_with_variants_data.append(variant_data)

    headers_mapping["product"]["collections"] = "collections"

    csv_headers_mapping = dict(ChainMap(*reversed(headers_mapping.values())))
    headers = (
        list(csv_headers_mapping.keys())
        + sorted(products_attributes_fields)
        + sorted(variants_attributes_fields)
        + sorted(warehouse_fields)
    )

    table = etl.fromdicts(products_with_variants_data, header=headers, missing=" ")
    table = etl.rename(table, csv_headers_mapping)

    etl.tocsv(table, file_name, delimiter=delimiter)


def update_product_data(
    product: "Product", product_data: Dict["str", Union["str", bool]],
) -> Tuple[dict, list]:
    product_data["collections"] = ", ".join(
        product.collections.values_list("slug", flat=True)
    )
    product_data["images"] = get_image_file_names(product)
    product_attributes_data = prepare_attributes_data(product)
    product_data.update(product_attributes_data)

    return product_data, product_attributes_data.keys()


def create_variant_data(
    variant: "ProductVariant", variant_data: Dict["str", Union["str", bool]]
) -> Tuple[dict, list, list]:
    variant_data["images"] = get_image_file_names(variant)
    variant_attribute_data = prepare_attributes_data(variant)
    variant_data.update(variant_attribute_data)

    warehouse_data = prepare_warehouse_data(variant)
    variant_data.update(warehouse_data)

    return variant_data, variant_attribute_data.keys(), warehouse_data.keys()


def get_image_file_names(instance: Union["Product", "ProductVariant"]):
    return ", ".join(
        [
            image.split("/")[1]
            for image in instance.images.values_list("image", flat=True)
        ]
    )


def prepare_attributes_data(instance: Union["Product", "ProductVariant"]):
    attribute_values = {}
    for assigned_attribute in instance.attributes.all():
        attribute_slug = assigned_attribute.attribute.slug
        attribute_header = f"{attribute_slug} (attribute)"
        attribute_values[attribute_header] = ", ".join(
            assigned_attribute.values.values_list("slug", flat=True)
        )
    return attribute_values


def prepare_warehouse_data(variant: "ProductVariant"):
    data = variant.stock.values("warehouse__slug", "quantity", "quantity_allocated")
    warehouse_data = {}
    for stock_data in data:
        warehouse_slug = stock_data["warehouse__slug"]
        warehouse_data[f"{warehouse_slug} (warehouse quantity)"] = stock_data[
            "quantity"
        ]
        warehouse_data[f"{warehouse_slug} (warehouse quantity allocated)"] = stock_data[
            "quantity_allocated"
        ]
    return warehouse_data

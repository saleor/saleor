from typing import TYPE_CHECKING, Dict, List, Set, Tuple, Union

import petl as etl

if TYPE_CHECKING:
    # flake8: noqa
    from ..product.models import Product, ProductVariant


def export_products(queryset, delimiter=";"):
    file_name = "product_data.csv"
    headers_mapping = {
        "product_type__name": "product_type",
        "category__slug": "category",
        "is_published": "visible",
        "price_amount": "price",
    }

    attributes_and_warehouse_fields = set()
    product_fields = ["id", "name", "description"] + list(headers_mapping.keys())
    variant_fields = ["sku"]

    products_with_variants_data = []
    products_data = queryset.values(*product_fields)

    for product, product_data in zip(queryset, products_data):
        product_data, product_attributes_fields = update_product_data(
            product, product_data
        )
        attributes_and_warehouse_fields.update(product_attributes_fields)
        products_with_variants_data.append(product_data)

        variants = product.variants.all()
        for variant in variants:
            variant_data, variant_specific_fields = create_variant_data(variant)
            attributes_and_warehouse_fields.update(variant_specific_fields)
            products_with_variants_data.append(variant_data)

    headers = product_fields + variant_fields + list(attributes_and_warehouse_fields)
    table = etl.fromdicts(products_with_variants_data, header=headers, missing="-")
    table = etl.rename(table, headers_mapping)

    etl.tocsv(table, file_name, delimiter=delimiter)


def update_product_data(
    product: "Product", product_data: Dict["str", Union["str", bool]],
) -> Tuple[dict, set]:
    product_data["collections"] = ", ".join(
        product.collections.values_list("slug", flat=True)
    )
    product_data["images"] = get_image_file_names(product)
    product_attributes_data = prepare_attributes_data(product)
    product_data.update(product_attributes_data)

    return product_data, product_attributes_data.keys()


def create_variant_data(variant: "ProductVariant"):
    variant_data = {"sku": variant.sku}
    variant_data["images"] = get_image_file_names(variant)
    variant_attribute_data = prepare_attributes_data(variant)
    variant_data.update(variant_attribute_data)

    warehouse_data = prepare_warehouse_data(variant)
    variant_data.update(warehouse_data)

    variant_fields = set(variant_attribute_data.keys())
    variant_fields.update(set(warehouse_data.keys()))

    return variant_data, variant_fields


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
        attribute_header = "attribute_{}".format(attribute_slug.replace("-", "_"))
        attribute_values[attribute_header] = ", ".join(
            assigned_attribute.values.values_list("slug", flat=True)
        )
    return attribute_values


def prepare_warehouse_data(variant: "ProductVariant"):
    data = variant.stock.values("warehouse__id", "quantity", "quantity_allocated")
    warehouse_data = {}
    for stock_data in data:
        warehouse_key = f"warehouse_{stock_data['warehouse__id']}"
        warehouse_data[f"{warehouse_key}_qty"] = stock_data["quantity"]
        warehouse_data[f"{warehouse_key}_qty_allocated"] = stock_data[
            "quantity_allocated"
        ]
    return warehouse_data

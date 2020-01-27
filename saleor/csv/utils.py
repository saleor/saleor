from typing import TYPE_CHECKING, Union

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

    attributes_fields = set()
    fields = ["id", "name", "description"] + headers_mapping.keys()
    products_with_variants_data = []
    products_data = queryset.values(*fields)

    for product, product_data in zip(queryset, products_data):
        product_data["collections"] = ", ".join(
            product.collections.values_list("slug", flat=True)
        )
        product_data["images"] = get_image_file_names(product)
        product_attributes_data = prepare_attributes_data(product)
        attributes_fields.update(product_attributes_data.keys())
        product_data.update(product_attributes_data)
        products_with_variants_data.append(product_data)

    fields += list(attributes_fields)
    table = etl.fromdicts(products_with_variants_data, header=fields, missing="-")
    table = etl.rename(table, headers_mapping)

    etl.tocsv(table, file_name, delimiter=delimiter)


def get_image_file_names(product: "Product"):
    return ", ".join(
        [
            image.split("/")[1]
            for image in product.images.values_list("image", flat=True)
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

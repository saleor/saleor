from collections import ChainMap
from datetime import datetime
from tempfile import NamedTemporaryFile
from typing import IO, TYPE_CHECKING, Callable, Dict, List, Set, Tuple, Union

import petl as etl
from django.db.models import F
from django.utils import timezone

from ...celeryconf import app
from ...core.utils import build_absolute_uri
from ...product.models import Product
from .. import JobStatus
from ..emails import send_link_to_download_csv_for_products
from ..models import Job

if TYPE_CHECKING:
    # flake8: noqa
    from ..product.models import ProductVariant
    from django.db.models import QuerySet


@app.task
def export_products(
    scope: Dict[str, Union[str, dict]], job_id: int, delimiter: str = ";"
):
    job = Job.objects.get(pk=job_id)
    queryset = get_product_queryset(scope)
    file_name = "product_data_{}.csv".format(datetime.now().strftime("%d_%m_%Y"))

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

    export_data, attributes_and_warehouse_headers = prepare_products_data(
        queryset, headers_mapping
    )

    headers_mapping["product"]["collections"] = "collections"

    csv_headers_mapping = dict(
        ChainMap(*reversed(headers_mapping.values()))  # type: ignore
    )
    headers = list(csv_headers_mapping.keys()) + attributes_and_warehouse_headers

    create_csv_file_and_update_job(
        export_data, headers, csv_headers_mapping, delimiter, job, file_name
    )

    send_link_to_download_csv_for_products(job)


def get_product_queryset(scope: Dict[str, Union[str, dict]]) -> "QuerySet":
    from ...graphql.product.filters import ProductFilter

    queryset = Product.objects.all()
    if "ids" in scope:
        queryset = Product.objects.filter(pk__in=scope["ids"])
    elif "filter" in scope:
        queryset = ProductFilter(data=scope["filter"], queryset=queryset).qs

    queryset = (
        queryset.order_by("pk")
        .select_related("product_type", "category")
        .prefetch_related("attributes", "variants", "collections", "images")
    )

    return queryset


def create_csv_file_and_update_job(
    export_data: Dict[str, str],
    headers: List[str],
    csv_headers_mapping: Dict[str, str],
    delimiter: str,
    job: Job,
    file_name: str,
):
    table = etl.fromdicts(export_data, header=headers, missing=" ")
    table = etl.rename(table, csv_headers_mapping)

    temporary_file = NamedTemporaryFile()
    etl.tocsv(table, temporary_file.name, delimiter=delimiter)

    update_job(job, temporary_file, file_name)

    # remove temporary file
    temporary_file.close()


def update_job(job: Job, temporary_file: IO[bytes], file_name: str):
    job.content_file.save(file_name, temporary_file)
    job.status = JobStatus.SUCCESS  # type:ignore
    job.ended_at = datetime.now(timezone.get_current_timezone())
    job.save()


def prepare_products_data(
    queryset: "QuerySet", headers_mapping: Dict[str, Dict[str, str]]
):
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

        variants = product.variants.all().prefetch_related("images")
        variants_data = variants.annotate(variant_currency=F("currency")).values(
            *headers_mapping["variant"].keys()
        )
        for variant, variant_data in zip(variants, variants_data):
            variant_data, attribute_data, warehouse_data = update_variant_data(
                variant, variant_data
            )
            variants_attributes_fields.update(attribute_data)
            warehouse_fields.update(warehouse_data)
            products_with_variants_data.append(variant_data)

    attributes_and_warehouse_headers = (
        sorted(products_attributes_fields)
        + sorted(variants_attributes_fields)
        + sorted(warehouse_fields)
    )

    return products_with_variants_data, attributes_and_warehouse_headers


def update_product_data(
    product: Product, product_data: Dict["str", Union["str", bool]]
) -> Tuple[dict, list]:
    product_data["collections"] = ", ".join(
        product.collections.values_list("slug", flat=True)
    )
    product_data["images"] = get_images_uris(product)
    product_attributes_data = prepare_attributes_data(product)
    product_data.update(product_attributes_data)

    return product_data, product_attributes_data.keys()


def update_variant_data(
    variant: "ProductVariant", variant_data: Dict["str", Union["str", bool]]
) -> Tuple[dict, list, list]:
    variant_data["images"] = get_images_uris(variant)
    variant_attribute_data = prepare_attributes_data(variant)
    variant_data.update(variant_attribute_data)

    warehouse_data = prepare_warehouse_data(variant)
    variant_data.update(warehouse_data)

    return variant_data, variant_attribute_data.keys(), warehouse_data.keys()


def get_images_uris(instance: Union[Product, "ProductVariant"]):
    image_uris = filter(
        None, [build_absolute_uri(image.image.url) for image in instance.images.all()]
    )
    return ", ".join(image_uris)


def prepare_attributes_data(instance: Union[Product, "ProductVariant"]):
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

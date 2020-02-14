from collections import ChainMap
from tempfile import NamedTemporaryFile
from typing import IO, TYPE_CHECKING, Dict, List, Set, Tuple, Union

import petl as etl
from django.db.models import F
from django.utils import timezone

from ...celeryconf import app
from ...core.utils import build_absolute_uri
from ...product.models import Product
from .. import JobStatus
from ..emails import send_email_with_link_to_download_csv
from ..models import Job

if TYPE_CHECKING:
    # flake8: noqa
    from ..product.models import ProductVariant
    from django.db.models import QuerySet


PRODUCT_HEADERS_MAPPING = {
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
    "product_many_to_many": {"collections": "collections"},
    "variant": {
        "sku": "sku",
        "price_override_amount": "price override",
        "cost_price_amount": "cost price",
        "variant_currency": "variant_currency",
    },
    "common": {"images": "images"},
}


def on_task_failure(self, exc, task_id, args, kwargs, einfo):
    job_id = args[0]
    update_job_when_task_finished(job_id, JobStatus.FAILED)


def on_task_success(self, retval, task_id, args, kwargs):
    job_id = args[0]
    update_job_when_task_finished(job_id, JobStatus.SUCCESS)


def update_job_when_task_finished(job_id: int, status: JobStatus):
    job = Job.objects.get(pk=job_id)
    job.status = status  # type: ignore
    job.ended_at = timezone.now()
    job.save(update_fields=["status", "ended_at"])


@app.task(on_success=on_task_success, on_failure=on_task_failure)
def export_products(
    job_id: int, scope: Dict[str, Union[str, dict]], delimiter: str = ";"
):
    file_name = get_filename("product")
    queryset = get_product_queryset(scope)

    export_data, attributes_and_warehouse_headers = prepare_products_data(
        queryset, PRODUCT_HEADERS_MAPPING
    )
    csv_headers_mapping = dict(
        ChainMap(*reversed(PRODUCT_HEADERS_MAPPING.values()))  # type: ignore
    )
    headers = list(csv_headers_mapping.keys()) + attributes_and_warehouse_headers

    job = Job.objects.get(pk=job_id)
    create_csv_file_and_save_to_job(
        export_data, headers, csv_headers_mapping, delimiter, job, file_name
    )
    send_email_with_link_to_download_csv(job, "export_products")


def get_filename(model_name: str):
    return "{}_data_{}.csv".format(model_name, timezone.now().strftime("%d_%m_%Y"))


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


def prepare_products_data(
    queryset: "QuerySet", headers_mapping: Dict[str, Dict[str, str]]
) -> Tuple[List[Dict[str, Union[str, bool]]], List[str]]:
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


def create_csv_file_and_save_to_job(
    export_data: List[Dict[str, Union[str, bool]]],
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

    save_csv_file_in_job(job, temporary_file, file_name)

    # remove temporary file
    temporary_file.close()


def save_csv_file_in_job(job: Job, temporary_file: IO[bytes], file_name: str):
    job.content_file.save(file_name, temporary_file)

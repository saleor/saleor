import os
from collections import ChainMap, defaultdict
from tempfile import NamedTemporaryFile
from typing import IO, TYPE_CHECKING, Dict, List, Optional, Set, Tuple, Union

import petl as etl
from django.conf import settings
from django.db.models import F
from django.utils import timezone

from ...celeryconf import app
from ...core.utils import build_absolute_uri
from ...product.models import Product, ProductVariant
from .. import JobStatus
from ..emails import send_email_with_link_to_download_csv
from ..models import Job

if TYPE_CHECKING:
    # flake8: noqa
    from django.db.models import QuerySet


class ProductExportFields:
    """Data structure with fields for product export."""

    PRODUCT_RELATION_FIELDS = [
        "attribute_value",
        "attribute_slug",
        "collections__slug",
        "image_path",
    ]
    WAREHOUSE_FIELDS = [
        "stock__warehouse__slug",
        "stock__quantity",
        "stock__quantity_allocated",
    ]
    ATTRIBUTE_FIELDS = ["slugs_of_values", "attribute_slug"]
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


MEDIA_URL = settings.MEDIA_URL


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
        queryset, ProductExportFields.PRODUCT_HEADERS_MAPPING
    )
    csv_headers_mapping = dict(
        ChainMap(*reversed(ProductExportFields.PRODUCT_HEADERS_MAPPING.values()))  # type: ignore
    )
    headers = list(csv_headers_mapping.keys()) + attributes_and_warehouse_headers

    job = Job.objects.get(pk=job_id)
    create_csv_file_and_save_in_job(
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

    queryset = queryset.order_by("pk").prefetch_related(
        "attributes", "variants", "collections", "images", "product_type", "category"
    )

    return queryset


def prepare_products_data(
    queryset: "QuerySet", headers_mapping: Dict[str, Dict[str, str]]
) -> Tuple[List[Dict[str, Union[str, bool]]], List[str]]:
    variants_attributes_fields: Set[str] = set()
    warehouse_fields: Set[str] = set()

    products_with_variants_data = []
    products_data = queryset.annotate(product_currency=F("currency")).values(
        *headers_mapping["product"].keys()
    )

    product_relations_data, products_attributes_fields = prepare_product_relations_data(
        queryset
    )

    for product_data in products_data:
        pk = product_data["id"]
        relations_data = product_relations_data.get(pk, {})
        data = {**product_data, **relations_data}

        products_with_variants_data.append(data)

        variants_data, *headers = prepare_variants_data(pk)
        products_with_variants_data.extend(variants_data)
        variants_attributes_fields.update(headers[0])
        warehouse_fields.update(headers[1])

    attributes_and_warehouse_headers: list = (
        sorted(products_attributes_fields)
        + sorted(variants_attributes_fields)
        + sorted(warehouse_fields)
    )

    return products_with_variants_data, attributes_and_warehouse_headers


def prepare_product_relations_data(
    queryset: "QuerySet",
) -> Tuple[Dict[int, Dict[str, str]], set]:
    product_fields = ProductExportFields.PRODUCT_RELATION_FIELDS + ["pk"]
    relations_data = queryset.annotate(
        attribute_value=F("attributes__values__slug"),
        attribute_slug=F("attributes__assignment__attribute__slug"),
        image_path=F("images__image"),
    ).values(*product_fields)

    attributes_headers = set()
    result_data: Dict[int, dict] = defaultdict(dict)
    for data in relations_data:
        pk = data.get("pk")
        attribute_data = {
            "slug": data["attribute_slug"],
            "value": data["attribute_value"],
        }
        collection = data.get("collections__slug")
        image = data.pop("image_path")

        result_data, attribute_header = add_attribute_info_to_data(
            pk, attribute_data, result_data
        )
        if attribute_header:
            attributes_headers.add(attribute_header)

        result_data = add_image_uris_to_data(pk, image, result_data)
        result_data = add_collection_info_to_data(pk, collection, result_data)

    result: Dict[int, Dict[str, str]] = {
        pk: {header: ", ".join(sorted(values)) for header, values in data.items()}
        for pk, data in result_data.items()
    }
    return result, attributes_headers


def add_collection_info_to_data(
    pk: int, collection: str, result_data: Dict[int, dict]
) -> Dict[int, dict]:
    if collection:
        header = "collections"
        if header in result_data[pk]:
            result_data[pk][header].add(collection)  # type: ignore
        else:
            result_data[pk][header] = {collection}
    return result_data


def prepare_variants_data(pk: int):
    variants = ProductVariant.objects.filter(product__pk=pk).prefetch_related(
        "images", "attributes"
    )
    fields = (
        ["pk", "image_path"]
        + list(ProductExportFields.PRODUCT_HEADERS_MAPPING["variant"].keys())
        + ProductExportFields.ATTRIBUTE_FIELDS
        + ProductExportFields.WAREHOUSE_FIELDS
    )
    variants_data = (
        variants.annotate(
            slugs_of_values=F("attributes__values__slug"),
            attribute_slug=F("attributes__assignment__attribute__slug"),
            variant_currency=F("currency"),
            image_path=F("images__image"),
        )
        .order_by("sku")
        .values(*fields)
    )

    result_data, variant_attributes_headers, warehouse_headers = update_variant_data(
        variants_data
    )

    result = [
        {
            header: ", ".join(sorted(values)) if isinstance(values, set) else values
            for header, values in data.items()
        }
        for pk, data in result_data.items()
    ]
    return result, variant_attributes_headers, warehouse_headers


def update_variant_data(
    variants_data: List[Dict[str, Union[str, int]]]
) -> Tuple[Dict[int, dict], set, set]:
    variant_attributes_headers = set()
    warehouse_headers = set()
    result_data: Dict[int, dict] = defaultdict(dict)
    for data in variants_data:
        pk: int = data.pop("pk")  # type: ignore
        attribute_data = {
            "slug": data.pop("attribute_slug"),
            "value": data.pop("slugs_of_values"),
        }
        warehouse_data = {
            "slug": data.pop("stock__warehouse__slug"),
            "qty": data.pop("stock__quantity"),
            "qty_alc": data.pop("stock__quantity_allocated"),
        }
        image: str = data.pop("image_path")  # type: ignore

        if pk not in result_data:
            result_data[pk] = data

        result_data, attribute_header = add_attribute_info_to_data(
            pk, attribute_data, result_data
        )
        if attribute_header:
            variant_attributes_headers.add(attribute_header)

        result_data, headers = add_warehouse_info_to_data(
            pk, warehouse_data, result_data
        )
        if headers:
            warehouse_headers.update(headers)

        result_data = add_image_uris_to_data(pk, image, result_data)

    return result_data, variant_attributes_headers, warehouse_headers


def add_image_uris_to_data(
    pk: int, image: str, result_data: Dict[int, dict]
) -> Dict[int, dict]:
    if image:
        header = "images"
        uri = build_absolute_uri(os.path.join(MEDIA_URL, image))
        if header in result_data[pk]:
            result_data[pk][header].add(uri)
        else:
            result_data[pk][header] = {uri}
    return result_data


def add_attribute_info_to_data(
    pk: int, attribute_data: Dict[str, Union[str, int]], result_data: Dict[int, dict],
) -> Tuple[Dict[int, dict], Optional[str]]:
    slug = attribute_data["slug"]
    header = None
    if slug:
        header = f"{slug} (attribute)"
        if header in result_data[pk]:
            result_data[pk][header].add(attribute_data["value"])  # type: ignore
        else:
            result_data[pk][header] = {attribute_data["value"]}
    return result_data, header


def add_warehouse_info_to_data(
    pk: int, warehouse_data: Dict[str, Union[str, int]], result_data: Dict[int, dict],
) -> Tuple[Dict[int, dict], set]:
    slug = warehouse_data["slug"]
    warehouse_headers: Set[str] = set()
    if slug:
        warehouse_qty_header = f"{slug} (warehouse quantity)"
        warehouse_qty_alc_header = f"{slug} (warehouse quantity allocated)"
        if warehouse_qty_header not in result_data[pk]:
            result_data[pk][warehouse_qty_header] = warehouse_data["qty"]
            result_data[pk][warehouse_qty_alc_header] = warehouse_data["qty_alc"]
            warehouse_headers = {warehouse_qty_header, warehouse_qty_alc_header}

    return result_data, warehouse_headers


def create_csv_file_and_save_in_job(
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

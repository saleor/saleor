from tempfile import NamedTemporaryFile
from typing import IO, TYPE_CHECKING, Dict, List, Set, Union

import petl as etl
from django.utils import timezone

from ...celeryconf import app
from ...core import JobStatus
from ...product.models import Product
from .. import FileTypes, events
from ..emails import send_email_with_link_to_download_csv, send_export_failed_info
from ..models import ExportFile
from .products_data import get_export_fields_and_headers_info, get_products_data

if TYPE_CHECKING:
    # flake8: noqa
    from django.db.models import QuerySet


BATCH_SIZE = 10000


def on_task_failure(self, exc, task_id, args, kwargs, einfo):
    export_file_id = args[0]
    export_file = ExportFile.objects.get(pk=export_file_id)

    export_file.content_file = None
    export_file.status = JobStatus.FAILED
    export_file.save(update_fields=["status", "updated_at", "content_file"])

    events.export_failed_event(
        export_file=export_file,
        user=export_file.created_by,
        message=str(exc),
        error_type=str(einfo.type),
    )
    send_export_failed_info(export_file, "export_failed")


def on_task_success(self, retval, task_id, args, kwargs):
    export_file_id = args[0]

    export_file = ExportFile.objects.get(pk=export_file_id)
    export_file.status = JobStatus.SUCCESS
    export_file.save(update_fields=["status", "updated_at"])

    events.export_success_event(export_file=export_file, user=export_file.created_by)


@app.task(on_success=on_task_success, on_failure=on_task_failure)
def export_products(
    export_file_id: int,
    scope: Dict[str, Union[str, dict]],
    export_info: Dict[str, list],
    file_type: str,
    delimiter: str = ";",
):
    file_name = get_filename("product", file_type)
    queryset = get_product_queryset(scope)

    export_fields, csv_headers_mapping, headers = get_export_fields_and_headers_info(
        export_info
    )
    export_file = ExportFile.objects.get(pk=export_file_id)

    export_products_in_batches(
        queryset,
        export_info,
        set(export_fields),
        headers,
        csv_headers_mapping,
        delimiter,
        export_file,
        file_name,
        file_type,
    )
    send_email_with_link_to_download_csv(export_file, "export_products_success")


def get_filename(model_name: str, file_type: str) -> str:
    return "{}_data_{}.{}".format(
        model_name, timezone.now().strftime("%d_%m_%Y"), file_type
    )


def get_product_queryset(scope: Dict[str, Union[str, dict]]) -> "QuerySet":
    """Get product queryset based on a scope."""

    from ...graphql.product.filters import ProductFilter

    queryset = Product.objects.all()
    if "ids" in scope:
        queryset = Product.objects.filter(pk__in=scope["ids"])
    elif "filter" in scope:
        queryset = ProductFilter(data=scope["filter"], queryset=queryset).qs

    queryset = queryset.order_by("pk")

    return queryset


def queryset_in_batches(queryset):
    """Slice a queryset into batches.

    Input queryset should be sorted be pk.
    """
    start_pk = 0

    while True:
        if not queryset.filter(pk__gt=start_pk).exists():
            break

        qs = queryset.filter(pk__gt=start_pk)

        pks = qs.values_list("pk", flat=True)
        try:
            end_pk = pks[BATCH_SIZE - 1]
        except IndexError:
            end_pk = pks.last()

        yield qs.filter(pk__lte=end_pk)

        start_pk = end_pk


def export_products_in_batches(
    queryset: "QuerySet",
    export_info: Dict[str, list],
    export_fields: Set[str],
    headers: List[str],
    csv_headers_mapping: Dict[str, str],
    delimiter: str,
    export_file: ExportFile,
    file_name: str,
    file_type: str,
):
    warehouses = export_info.get("warehouses")
    attributes = export_info.get("attributes")

    create_file = True

    for batch in queryset_in_batches(queryset):
        product_batch = batch.prefetch_related(
            "attributes",
            "variants",
            "collections",
            "images",
            "product_type",
            "category",
        )

        export_data = get_products_data(
            product_batch, export_fields, warehouses, attributes,
        )

        if create_file:
            create_csv_file_and_save_in_export_file(
                export_data,
                headers,
                csv_headers_mapping,
                delimiter,
                export_file,
                file_name,
                file_type,
            )
            create_file = False
        else:
            append_to_file(export_data, headers, export_file, file_type, delimiter)

    send_email_with_link_to_download_csv(export_file, "export_products")


def create_csv_file_and_save_in_export_file(
    export_data: List[Dict[str, Union[str, bool]]],
    headers: List[str],
    csv_headers_mapping: Dict[str, str],
    delimiter: str,
    export_file: ExportFile,
    file_name: str,
    file_type: str,
):
    table = etl.fromdicts(export_data, header=headers, missing=" ")
    table = etl.rename(table, csv_headers_mapping)

    with NamedTemporaryFile() as temporary_file:
        if file_type == FileTypes.CSV:
            etl.tocsv(table, temporary_file.name, delimiter=delimiter)
        else:
            etl.io.xlsx.toxlsx(table, temporary_file.name)

        save_csv_file_in_export_file(export_file, temporary_file, file_name)


def append_to_file(
    export_data: List[Dict[str, Union[str, bool]]],
    headers: List[str],
    export_file: ExportFile,
    file_type: str,
    delimiter: str,
):
    table = etl.fromdicts(export_data, header=headers, missing=" ")

    if file_type == FileTypes.CSV:
        etl.io.csv.appendcsv(table, export_file.content_file, delimiter=delimiter)
    else:
        etl.io.xlsx.appendxlsx(table, export_file.content_file.path)


def save_csv_file_in_export_file(
    export_file: ExportFile, temporary_file: IO[bytes], file_name: str
):
    export_file.content_file.save(file_name, temporary_file)

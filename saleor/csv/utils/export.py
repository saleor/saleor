from tempfile import NamedTemporaryFile
from typing import IO, TYPE_CHECKING, Dict, List, Union

import petl as etl
from django.utils import timezone

from ...celeryconf import app
from ...core import JobStatus
from ...product.models import Product
from .. import FileTypes, events
from ..emails import send_email_with_link_to_download_csv
from ..models import ExportFile
from .products_data import get_products_data

if TYPE_CHECKING:
    # flake8: noqa
    from django.db.models import QuerySet


def on_task_failure(self, exc, task_id, args, kwargs, einfo):
    export_file_id = args[0]
    export_file = ExportFile.objects.get(pk=export_file_id)
    update_export_file_when_task_finished(export_file, JobStatus.FAILED)
    events.export_failed_event(
        export_file=export_file,
        user=export_file.created_by,
        message=str(exc),
        error_type=str(einfo.type),
    )


def on_task_success(self, retval, task_id, args, kwargs):
    export_file_id = args[0]
    export_file = ExportFile.objects.get(pk=export_file_id)
    update_export_file_when_task_finished(export_file, JobStatus.SUCCESS)
    events.export_success_event(export_file=export_file, user=export_file.created_by)


def update_export_file_when_task_finished(export_file: ExportFile, status: JobStatus):
    export_file.status = status  # type: ignore
    export_file.save(update_fields=["status", "updated_at"])


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

    export_data, csv_headers_mapping, headers = get_products_data(queryset, export_info)

    export_file = ExportFile.objects.get(pk=export_file_id)
    create_csv_file_and_save_in_export_file(
        export_data,
        headers,
        csv_headers_mapping,
        delimiter,
        export_file,
        file_name,
        file_type,
    )
    send_email_with_link_to_download_csv(export_file, "export_products")


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

    queryset = queryset.order_by("pk").prefetch_related(
        "attributes", "variants", "collections", "images", "product_type", "category"
    )

    return queryset


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


def save_csv_file_in_export_file(
    export_file: ExportFile, temporary_file: IO[bytes], file_name: str
):
    export_file.content_file.save(file_name, temporary_file)

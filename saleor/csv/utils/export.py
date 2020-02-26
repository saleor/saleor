from tempfile import NamedTemporaryFile
from typing import IO, TYPE_CHECKING, Dict, List, Union

import petl as etl
from django.utils import timezone

from ...celeryconf import app
from ...product.models import Product
from .. import JobStatus
from ..emails import send_email_with_link_to_download_csv
from ..models import Job
from .products_data import get_products_data

if TYPE_CHECKING:
    # flake8: noqa
    from django.db.models import QuerySet


def on_task_failure(self, exc, task_id, args, kwargs, einfo):
    job_id = args[0]
    update_job_when_task_finished(job_id, JobStatus.FAILED)


def on_task_success(self, retval, task_id, args, kwargs):
    job_id = args[0]
    update_job_when_task_finished(job_id, JobStatus.SUCCESS)


def update_job_when_task_finished(job_id: int, status: JobStatus):
    job = Job.objects.get(pk=job_id)
    job.status = status  # type: ignore
    job.completed_at = timezone.now()
    job.save(update_fields=["status", "completed_at"])


@app.task(on_success=on_task_success, on_failure=on_task_failure)
def export_products(
    job_id: int, scope: Dict[str, Union[str, dict]], delimiter: str = ";"
):
    file_name = get_filename("product")
    queryset = get_product_queryset(scope)

    export_data, csv_headers_mapping, headers = get_products_data(queryset)

    job = Job.objects.get(pk=job_id)
    create_csv_file_and_save_in_job(
        export_data, headers, csv_headers_mapping, delimiter, job, file_name
    )
    send_email_with_link_to_download_csv(job, "export_products")


def get_filename(model_name: str) -> str:
    return "{}_data_{}.csv".format(model_name, timezone.now().strftime("%d_%m_%Y"))


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

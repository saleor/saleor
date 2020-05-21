from typing import Union

from django.core.files.storage import default_storage
from django.http import FileResponse, HttpResponseNotFound


def download_invoice(
    request, invoice_hash: str
) -> Union[FileResponse, HttpResponseNotFound]:
    """Serve file object with invoice."""
    try:
        invoice_file_object = default_storage.open(f"{invoice_hash}.pdf")
    except (FileNotFoundError, TypeError):
        return HttpResponseNotFound()

    response = FileResponse(invoice_file_object)
    response["Content-Length"] = len(invoice_file_object)
    response["Content-Type"] = "application/pdf"
    response["Content-Disposition"] = 'attachment; filename="{}"'.format(
        f"{invoice_hash}.pdf"
    )
    return response

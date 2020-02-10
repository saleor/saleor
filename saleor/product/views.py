import mimetypes
import os
from typing import Union

from django.http import FileResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404

from .models import DigitalContentUrl
from .utils.digital_products import (
    digital_content_url_is_valid,
    increment_download_count,
)


def digital_product(request, token: str) -> Union[FileResponse, HttpResponseNotFound]:
    """Return the direct download link to content if given token is still valid."""

    qs = DigitalContentUrl.objects.prefetch_related("line__order__user")
    content_url = get_object_or_404(qs, token=token)  # type: DigitalContentUrl
    if not digital_content_url_is_valid(content_url):
        return HttpResponseNotFound("Url is not valid anymore")

    digital_content = content_url.content
    digital_content.content_file.open()
    opened_file = digital_content.content_file.file
    filename = os.path.basename(digital_content.content_file.name)
    file_expr = 'filename="{}"'.format(filename)

    content_type = mimetypes.guess_type(str(filename))[0]
    response = FileResponse(opened_file)
    response["Content-Length"] = digital_content.content_file.size

    response["Content-Type"] = str(content_type)
    response["Content-Disposition"] = "attachment; {}".format(file_expr)

    increment_download_count(content_url)
    return response

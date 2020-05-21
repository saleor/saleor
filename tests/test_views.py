from unittest.mock import MagicMock, patch
from uuid import uuid4

from django.core.files import File
from django.http import FileResponse
from django.urls import reverse


@patch("saleor.order.views.default_storage.open")
def test_download_invoice(storage_mock, client):
    storage_mock.return_value = MagicMock(spec=File)
    url = reverse("download-invoice", args=[uuid4()])
    response = client.get(url)
    assert response.status_code == 200
    assert isinstance(response, FileResponse)


def test_download_invoice_non_existing_uuid(client):
    url = reverse("download-invoice", args=[uuid4()])
    response = client.get(url)
    assert response.status_code == 404

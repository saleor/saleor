import functools
from pathlib import Path

import jwt
import pytest
from django.http import FileResponse, Http404
from django.test import RequestFactory
from jwt import PyJWK

from ..jwt_manager import get_jwt_manager
from ..views import serve_media_view


@pytest.fixture
def dummy_media_file_request(media_root: str):
    # Create a dummy empty image file
    filename = "image.png"
    (file := (Path(media_root) / filename)).touch(mode=0o600, exist_ok=False)

    # Return HTTP request to that file
    yield RequestFactory().get(f"/media/{filename}")

    # Delete
    file.unlink(missing_ok=False)


def test_jwks_can_be_used_to_decode_saleor_token(client):
    # given
    jwt_manager = get_jwt_manager()
    payload = {"A": "1", "B": "2", "C": "3"}
    token = jwt_manager.encode(payload)

    # when
    response = client.get("/.well-known/jwks.json")
    key = response.json().get("keys")[0]

    # then
    jwt.decode(token, PyJWK.from_dict(key, algorithm="RS256").key, algorithms=["RS256"])


def test_serve_media_view_serves_as_attachment(
    settings, media_root: str, dummy_media_file_request
):
    """Ensure the view returns ``Content-Disposition: attachment``."""

    settings.DEBUG = True
    send_request = functools.partial(
        serve_media_view,
        dummy_media_file_request,
        document_root=media_root,
    )

    # Should add the header when the file is found
    response = send_request(path="image.png")
    assert isinstance(response, FileResponse)
    assert response.headers["Content-Disposition"] == "attachment"

    # Shouldn't add the header when not found, it should just raise
    with pytest.raises(Http404):
        send_request(path="image2.png")


def test_serve_media_view_serves_only_when_debug_mode(
    settings, media_root: str, dummy_media_file_request
):
    """Ensure the view only serves content when DEBUG=True."""

    send_request = functools.partial(
        serve_media_view,
        dummy_media_file_request,
        path="image.png",
        document_root=media_root,
    )

    # Ensure when DEBUG=True, it should serve the files
    settings.DEBUG = True
    response = send_request()
    assert isinstance(response, FileResponse)
    assert response.status_code == 200

    # When DEBUG=False, it should just return HTTP 404
    settings.DEBUG = False
    with pytest.raises(Http404):
        response = send_request()

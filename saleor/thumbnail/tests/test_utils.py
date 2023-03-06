from unittest.mock import MagicMock

import graphene
import pytest
from django.core.files import File

from ..models import Thumbnail
from ..utils import (
    get_image_or_proxy_url,
    get_thumbnail_size,
    prepare_image_proxy_url,
    prepare_thumbnail_file_name,
)


@pytest.mark.parametrize(
    "size, expected_value",
    [(1, 32), (16, 32), (60, 64), (80, 64), (256, 256), (8000, 4096), (15000, 4096)],
)
def test_get_thumbnail_size(size, expected_value):
    # when
    returned_size = get_thumbnail_size(size)

    # then
    assert returned_size == expected_value


@pytest.mark.parametrize(
    "file_name, size, format, expected_name",
    [
        ("test.txt", 20, None, "test_thumbnail_20.txt"),
        ("test/test.txt", 20, None, "test/test_thumbnail_20.txt"),
        ("test/test.txt", 40, "webp", "test/test_thumbnail_40.webp"),
        (
            "test/test_23.03.2022.txt",
            40,
            "webp",
            "test/test_23.03.2022_thumbnail_40.webp",
        ),
    ],
)
def test_prepare_thumbnail_file_name(file_name, size, format, expected_name):
    # when
    thumbnail_name = prepare_thumbnail_file_name(file_name, size, format)

    # then
    assert thumbnail_name == expected_name


@pytest.mark.parametrize(
    "size, format", [(100, "WEBP"), (1, None), (200, ""), (64, "AVIF")]
)
def test_prepare_image_proxy_url(size, format, collection):
    # given
    instance_id = graphene.Node.to_global_id("Collection", collection.id)

    # when
    url = prepare_image_proxy_url(collection.id, "Collection", size, format)

    # then
    expected_url = f"/thumbnail/{instance_id}/{size}/"
    if format:
        expected_url += f"{format.lower()}/"
    assert url == expected_url


def test_get_image_or_proxy_url_proxy_url_returned(collection):
    # given
    size = 128
    format = None

    # when
    url = get_image_or_proxy_url(None, collection.id, "Collection", size, format)

    # then
    instance_id = graphene.Node.to_global_id("Collection", collection.id)
    assert url == f"/thumbnail/{instance_id}/{size}/"


def test_get_image_or_proxy_url_thumbnail_url_returned(collection, media_root):
    # given
    size = 128
    format = None

    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    thumbnail = Thumbnail.objects.create(
        collection=collection, size=128, image=thumbnail_mock
    )

    # when
    url = get_image_or_proxy_url(thumbnail, collection.id, "Collection", size, format)

    # then
    assert url == thumbnail.image.url

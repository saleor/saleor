from io import BytesIO
from unittest.mock import Mock

import pytest
from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError

from .. import MIN_ICON_SIZE
from ..validators import (
    validate_icon_image,
    validate_image_exif,
    validate_image_format,
    validate_image_size,
)


@pytest.fixture
def image_factory():
    def factory(format="JPEG", size=(1, 1)):
        image = Image.new("RGB", size=size)
        image.format = format
        return image

    return factory


def test_validate_image_format(image_factory):
    validate_image_format(image_factory(), "invalid")


def test_validate_image_format_when_not_allowed(image_factory):
    image, error_code = image_factory(), "invalid"
    with pytest.raises(ValidationError) as err:
        validate_image_format(image, error_code, allowed_mimetypes=[])
    assert err.value.code == error_code


def test_validate_image_exif(image_factory):
    image, error_code = image_factory(), "invalid"
    image.getexif = Mock(side_effect=UnidentifiedImageError)
    with pytest.raises(ValidationError) as err:
        validate_image_exif(image, error_code)
    assert err.value.code == error_code


def test_validate_image_size(image_factory):
    image, error_code = image_factory(), "invalid"
    validate_image_size(image, error_code, 1, None, True)


@pytest.mark.parametrize(
    ("size", "min_size", "max_size", "square_required"),
    [
        ((1, 1), 10, None, False),
        ((2, 2), None, 1, False),
        ((1, 2), None, None, True),
    ],
)
def test_validate_image_size_with_invalid_image(
    image_factory, size, min_size, max_size, square_required
):
    image = image_factory(size=size)
    error_code = "invalid"
    with pytest.raises(ValidationError) as err:
        validate_image_size(image, error_code, min_size, max_size, square_required)
    assert err.value.code == error_code


def test_validate_icon_image(image_factory):
    img_data, image = BytesIO(), image_factory(size=(MIN_ICON_SIZE, MIN_ICON_SIZE))
    image.save(img_data, format="PNG")
    validate_icon_image(img_data, "invalid")


def test_validate_icon_image_with_invalid_image():
    img_data, error_code = BytesIO(b"data"), "invalid"
    with pytest.raises(ValidationError) as err:
        validate_icon_image(img_data, error_code)
    assert err.value.code == error_code

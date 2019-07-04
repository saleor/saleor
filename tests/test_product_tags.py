from unittest.mock import Mock, patch

import pytest
from django.templatetags.static import static
from django.test import override_settings

from saleor.product.templatetags.product_images import (
    choose_placeholder,
    get_product_image_thumbnail,
    get_thumbnail,
)


@override_settings(VERSATILEIMAGEFIELD_SETTINGS={"create_images_on_demand": True})
def test_get_thumbnail():
    instance = Mock()
    cropped_value = Mock(url="crop.jpg")
    thumbnail_value = Mock(url="thumb.jpg")
    instance.crop = {"10x10": cropped_value}
    instance.thumbnail = {"10x10": thumbnail_value}
    cropped = get_thumbnail(instance, 10, method="crop")
    assert cropped == cropped_value.url
    thumb = get_thumbnail(instance, 10, method="thumbnail")
    assert thumb == thumbnail_value.url


def test_get_thumbnail_no_instance(monkeypatch):
    monkeypatch.setattr(
        "saleor.product.templatetags.product_images.choose_placeholder",
        lambda x: "placeholder",
    )
    output = get_thumbnail(image_file=None, size=10, method="crop")
    assert output == static("placeholder")


def test_get_product_image_thumbnail_no_instance(monkeypatch):
    monkeypatch.setattr(
        "saleor.product.templatetags.product_images.choose_placeholder",
        lambda x: "placeholder",
    )
    output = get_product_image_thumbnail(instance=None, size=10, method="crop")
    assert output == static("placeholder")


@patch(
    "saleor.product.templatetags.product_images.AVAILABLE_SIZES",
    {
        "products": (
            "thumbnail__800x800",
            "crop__100x100",
            "crop__1000x1000",
            "crop__2000x2000",
        )
    },
)
@override_settings(VERSATILEIMAGEFIELD_SETTINGS={"create_images_on_demand": False})
def test_get_thumbnail_to_larger():
    instance = Mock()
    cropped_value = Mock(url="crop.jpg")
    instance.crop = {"1000x1000": cropped_value}
    cropped = get_thumbnail(instance, 800, method="crop")
    assert cropped == cropped_value.url


@patch(
    "saleor.product.templatetags.product_images.AVAILABLE_SIZES",
    {
        "products": (
            "crop__10x10",
            "crop__100x100",
            "crop__1000x1000",
            "crop__2000x2000",
        )
    },
)
@override_settings(VERSATILEIMAGEFIELD_SETTINGS={"create_images_on_demand": False})
def test_get_thumbnail_to_smaller():
    instance = Mock()
    cropped_value = Mock(url="crop.jpg")
    instance.crop = {"100x100": cropped_value}
    cropped = get_thumbnail(instance, 400, method="crop")
    assert cropped == cropped_value.url


@patch(
    "saleor.product.templatetags.product_images.AVAILABLE_SIZES",
    {"products": ("thumbnail__800x800",)},
)
@override_settings(
    VERSATILEIMAGEFIELD_SETTINGS={"create_images_on_demand": False},
    PLACEHOLDER_IMAGES={1080: "images/placeholder1080x1080.png"},
)
def test_get_thumbnail_no_match_by_method():
    instance = Mock()
    cropped_value = Mock(url="crop.jpg")
    instance.crop = {"1000x1000": cropped_value}
    with pytest.warns(UserWarning) as record:
        cropped = get_thumbnail(instance, 800, method="crop")

    assert len(record) == 1
    assert (
        str(record[0].message)
        == "Thumbnail size crop__800x800 is not defined in settings"
        " and it won't be generated automatically"
    )
    assert cropped == static("images/placeholder1080x1080.png")


def test_choose_placeholder(settings):
    settings.PLACEHOLDER_IMAGES = {
        10: "10_placeholder",
        20: "20_placeholder",
        30: "30_placeholder",
    }

    settings.DEFAULT_PLACEHOLDER = "default_placeholder"

    # wrong or no size returns default
    assert choose_placeholder("wrong") == settings.DEFAULT_PLACEHOLDER
    assert choose_placeholder() == settings.DEFAULT_PLACEHOLDER

    # exact size
    assert choose_placeholder("10x10") == settings.PLACEHOLDER_IMAGES[10]

    # when exact not found, choose bigger available
    assert choose_placeholder("15x15") == settings.PLACEHOLDER_IMAGES[20]

    # like previous, but only one side bigger
    assert choose_placeholder("10x15") == settings.PLACEHOLDER_IMAGES[20]

    # when too big requested, choose the biggest available
    assert choose_placeholder("1500x1500") == settings.PLACEHOLDER_IMAGES[30]

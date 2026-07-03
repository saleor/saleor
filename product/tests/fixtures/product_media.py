import pytest

from ... import ProductMediaTypes
from ...models import ProductMedia


@pytest.fixture
def product_media_image(product, image, media_root):
    return ProductMedia.objects.create(
        product=product,
        image=image,
        alt="image",
        type=ProductMediaTypes.IMAGE,
        oembed_data="{}",
    )


@pytest.fixture
def product_media_image_not_yet_fetched(product):
    return ProductMedia.objects.create(
        product=product,
        type=ProductMediaTypes.IMAGE,
        external_url="https://example.com/image.jpg",
    )


@pytest.fixture
def product_media_video(product):
    return ProductMedia.objects.create(
        product=product,
        type=ProductMediaTypes.VIDEO,
        external_url="https://example.com/video.mp4",
    )

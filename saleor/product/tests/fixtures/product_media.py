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

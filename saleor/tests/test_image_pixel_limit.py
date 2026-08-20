from django.conf import settings
from PIL import Image


def test_pillow_pixel_limit_enforces_max_image_pixels():
    """Pillow must reject exactly at `settings.MAX_IMAGE_PIXELS`.

    Pillow warns above `Image.MAX_IMAGE_PIXELS` but only raises above twice that value,
    so settings halve the limit. Dropping the halving would silently double the number
    of pixels we are willing to decode.
    """
    assert Image.MAX_IMAGE_PIXELS == settings.MAX_IMAGE_PIXELS // 2

import logging
import re
import warnings

from django import template
from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static

from io import BytesIO
from PIL import Image
from versatileimagefield.datastructures import SizedImage
from versatileimagefield.registry import versatileimagefield_registry

logger = logging.getLogger(__name__)
register = template.Library()


class ThumbnailImage(SizedImage):
    filename_key = 'fitted'

    def __init__(self, *args, **kwargs):
        super(ThumbnailImage, self).__init__(*args, **kwargs)
        self.rgb = (255, 255, 255)

    def process_image(self, image, image_format, save_kwargs, width, height):
        imagefile = BytesIO()

        size = (width, height)

        image.thumbnail(size, Image.ANTIALIAS)

        offset_x = max((size[0] - image.size[0]) // 2, 0)
        offset_y = max((size[1] - image.size[1]) // 2, 0)
        offset_tuple = (offset_x, offset_y)  # pack x and y into a tuple

        # create the image object to be the final product
        final_thumb = Image.new(mode='RGB', size=size, color=self.rgb)

        # paste the thumbnail into the full sized image
        final_thumb.paste(image, offset_tuple)

        # save (the PNG format will retain the alpha band unlike JPEG)
        final_thumb.save(imagefile, **save_kwargs)

        return imagefile


versatileimagefield_registry.register_sizer('fit', ThumbnailImage)


# cache available sizes at module level
def get_available_sizes():
    all_sizes = set()
    keys = settings.VERSATILEIMAGEFIELD_RENDITION_KEY_SETS
    for dummy_size_group, sizes in keys.items():
        for dummy_size_name, size in sizes:
            all_sizes.add(size)
    return all_sizes


AVAILABLE_SIZES = get_available_sizes()


def choose_placeholder(size=''):
    # type: (str) -> str
    """Assign a placeholder at least as big as provided size if possible.

    When size is bigger than available, return the biggest.
    If size is invalid or not provided, return DEFAULT_PLACEHOLDER.
    """
    placeholder = settings.DEFAULT_PLACEHOLDER
    parsed_sizes = re.match(r'(\d+)x(\d+)', size)
    available_sizes = sorted(settings.PLACEHOLDER_IMAGES.keys())
    if parsed_sizes and available_sizes:
        # check for placeholder equal or bigger than requested picture
        x_size, y_size = parsed_sizes.groups()
        max_size = max([int(x_size), int(y_size)])
        bigger_or_eq = list(filter(lambda x: x >= max_size, available_sizes))
        if bigger_or_eq:
            placeholder = settings.PLACEHOLDER_IMAGES[bigger_or_eq[0]]
        else:
            placeholder = settings.PLACEHOLDER_IMAGES[available_sizes[-1]]
    return placeholder


@register.simple_tag()
def get_thumbnail(instance, size, method='crop'):
    size_name = '%s__%s' % (method, size)
    on_demand = settings.VERSATILEIMAGEFIELD_SETTINGS[
        'create_images_on_demand']
    if instance:
        if size_name not in AVAILABLE_SIZES and not on_demand:
            msg = (
                "Thumbnail size %s is not defined in settings "
                "and it won't be generated automatically" % size_name)
            warnings.warn(msg)
        try:
            thumbnail = getattr(instance, method)[size]
        except Exception:
            logger.exception(
                'Thumbnail fetch failed',
                extra={'instance': instance, 'size': size})
        else:
            return thumbnail.url
    return static(choose_placeholder(size))


@register.simple_tag()
def product_first_image(product, size, method='crop'):
    """Return the main image of the given product."""
    all_images = product.images.all() if product else []
    main_image = all_images[0].image if all_images else None
    return get_thumbnail(main_image, size, method)

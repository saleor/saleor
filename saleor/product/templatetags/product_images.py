import logging
import warnings

from django import template
from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static

logger = logging.getLogger(__name__)
register = template.Library()


# cache available sizes at module level
def get_available_sizes():
    all_sizes = set()
    keys = settings.VERSATILEIMAGEFIELD_RENDITION_KEY_SETS
    for size_group, sizes in keys.items():
        for size_name, size in sizes:
            all_sizes.add(size)
    return all_sizes

AVAILABLE_SIZES = get_available_sizes()


@register.simple_tag()
def get_thumbnail(instance, size, method='crop'):
    if instance:
        size_name = '%s__%s' % (method, size)
        if (size_name not in AVAILABLE_SIZES and not
            settings.VERSATILEIMAGEFIELD_SETTINGS['create_images_on_demand']):
            msg = ('Thumbnail size %s is not defined in settings '
                   'and it won\'t be generated automatically' % size_name)
            warnings.warn(msg)
        try:
            if method == 'crop':
                thumbnail = instance.crop[size]
            else:
                thumbnail = instance.thumbnail[size]
        except:
            logger.exception('Thumbnail fetch failed',
                             extra={'instance': instance, 'size': size})
        else:
            return thumbnail.url
    return static('images/product-image-placeholder.png')


@register.simple_tag()
def product_first_image(product, size, method='crop'):
    """
    Returns main product image
    """
    all_images = product.images.all()
    main_image = all_images[0].image if all_images else None
    return get_thumbnail(main_image, size, method)

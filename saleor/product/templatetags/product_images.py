import logging
import warnings

from django.template.context_processors import static
from django import template
from django.conf import settings

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
def product_image(instance, size, method='crop'):
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
    return static('dist/images/product-image-placeholder.png')

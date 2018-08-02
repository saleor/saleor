import logging
import re
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


def get_thumbnail_size(size, method):
    """ Return closest larger size if not more than 2 times larger, otherwise
    return closest smaller size
    """
    closest_larger = float('inf')
    closest_smaller = 0
    for available_size in AVAILABLE_SIZES:
        available_method, avail_size_str = available_size.split('__')
        width, height = [int(s) for s in avail_size_str.split('x')]
        avail_min_dim = min(width, height)

        if available_method != method:
            continue
        if size < avail_min_dim <= size * 2:
            closest_larger = min(avail_min_dim, closest_larger)
        if avail_min_dim <= size:
            closest_smaller = max(avail_min_dim, closest_smaller)

    if closest_larger != float('inf'):
        return '%sx%s' % (closest_larger, closest_larger)
    elif closest_smaller:
        return'%sx%s' % (closest_smaller, closest_smaller)
    else:
        return None


@register.simple_tag()
def get_thumbnail(instance, size, method='crop'):
    size_str = '%sx%s' % (size, size)
    size_name = '%s__%s' % (method, size_str)
    on_demand = settings.VERSATILEIMAGEFIELD_SETTINGS[
        'create_images_on_demand']
    if instance:
        used_size = size_str
        if size_name not in AVAILABLE_SIZES and not on_demand:
            used_size = get_thumbnail_size(size, method)
            if not used_size:
                msg = (
                    "Thumbnail size %s is not defined in settings "
                    "and it won't be generated automatically" % size_name)
                warnings.warn(msg)
        try:
            thumbnail = getattr(instance, method)[used_size]
        except Exception:
            logger.exception(
                'Thumbnail fetch failed',
                extra={'instance': instance, 'size': size})
        else:
            return thumbnail.url
    return static(choose_placeholder(size_str))


@register.simple_tag()
def product_first_image(product, size, method='crop'):
    """Return the main image of the given product."""
    all_images = product.images.all() if product else []
    main_image = all_images[0].image if all_images else None
    return get_thumbnail(main_image, size, method)

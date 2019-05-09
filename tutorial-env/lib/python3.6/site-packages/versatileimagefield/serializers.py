from __future__ import unicode_literals

from django.utils import six

from rest_framework.serializers import ImageField

from .utils import (
    build_versatileimagefield_url_set,
    get_rendition_key_set,
    validate_versatileimagefield_sizekey_list
)


class VersatileImageFieldSerializer(ImageField):
    """
    Returns a dictionary of urls corresponding to self.sizes
    - `image_instance`: A VersatileImageFieldFile instance
    - `self.sizes`: An iterable of 2-tuples, both strings. Example:
    [
        ('large', 'url'),
        ('medium', 'crop__400x400'),
        ('small', 'thumbnail__100x100')
    ]

    The above would lead to the following response:
    {
        'large': 'http://some.url/image.jpg',
        'medium': 'http://some.url/__sized__/image-crop-400x400.jpg',
        'small': 'http://some.url/__sized__/image-thumbnail-100x100.jpg',
    }
    """
    read_only = True

    def __init__(self, sizes, *args, **kwargs):
        if isinstance(sizes, six.string_types):
            sizes = get_rendition_key_set(sizes)
        self.sizes = validate_versatileimagefield_sizekey_list(sizes)
        super(VersatileImageFieldSerializer, self).__init__(
            *args, **kwargs
        )

    def to_native(self, value):
        """For djangorestframework <=2.3.14"""
        context_request = None
        if self.context:
            context_request = self.context.get('request', None)
        return build_versatileimagefield_url_set(
            value,
            self.sizes,
            request=context_request
        )

    def to_representation(self, value):
        """
        For djangorestframework >= 3
        """
        return self.to_native(value)

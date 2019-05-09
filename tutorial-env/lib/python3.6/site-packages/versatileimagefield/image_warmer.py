from __future__ import unicode_literals

from functools import reduce
import logging
from sys import stdout

from django.db.models import Model
from django.db.models.query import QuerySet
from django.utils import six

from .utils import (
    get_rendition_key_set,
    get_url_from_image_key,
    validate_versatileimagefield_sizekey_list
)

logger = logging.getLogger(__name__)


def cli_progress_bar(start, end, bar_length=50):
    """
    Prints out a Yum-style progress bar (via sys.stdout.write).
    `start`: The 'current' value of the progress bar.
    `end`: The '100%' value of the progress bar.
    `bar_length`: The size of the overall progress bar.

    Example output with start=20, end=100, bar_length=50:
    [###########----------------------------------------] 20/100 (100%)

    Intended to be used in a loop. Example:
    end = 100
    for i in range(end):
        cli_progress_bar(i, end)

    Based on an implementation found here:
        http://stackoverflow.com/a/13685020/1149774
    """
    percent = float(start) / end
    hashes = '#' * int(round(percent * bar_length))
    spaces = '-' * (bar_length - len(hashes))
    stdout.write(
        "\r[{0}] {1}/{2} ({3}%)".format(
            hashes + spaces,
            start,
            end,
            int(round(percent * 100))
        )
    )
    stdout.flush()


class VersatileImageFieldWarmer(object):
    """
    A class for creating sets of images from a VersatileImageField
    """

    def __init__(self, instance_or_queryset,
                 rendition_key_set, image_attr, verbose=False):
        """
        Arguments:
        `instance_or_queryset`: A django model instance or QuerySet
        `rendition_key_set`: Either a string that corresponds to a key on
                        settings.VERSATILEIMAGEFIELD_RENDITION_KEY_SETS
                        or an iterable
                        of 2-tuples, both strings:
            [0]: The 'name' of the image size.
            [1]: A VersatileImageField 'size_key'.
            Example: [
                ('large', 'url'),
                ('medium', 'crop__400x400'),
                ('small', 'thumbnail__100x100')
            ]
        `image_attr`: A dot-notated path to a VersatileImageField on
                      `instance_or_queryset`
        `verbose`: bool signifying whether a progress bar should be printed
                   to sys.stdout
        """
        if isinstance(instance_or_queryset, Model):
            queryset = instance_or_queryset.__class__._default_manager.filter(
                pk=instance_or_queryset.pk
            )
        elif isinstance(instance_or_queryset, QuerySet):
            queryset = instance_or_queryset
        else:
            raise ValueError(
                "Only django model instances or QuerySets can be processed by "
                "{}".format(self.__class__.__name__)
            )
        self.queryset = queryset
        if isinstance(rendition_key_set, six.string_types):
            rendition_key_set = get_rendition_key_set(rendition_key_set)
        self.size_key_list = [
            size_key
            for key, size_key in validate_versatileimagefield_sizekey_list(
                rendition_key_set
            )
        ]
        self.image_attr = image_attr
        self.verbose = verbose

    @staticmethod
    def _prewarm_versatileimagefield(size_key, versatileimagefieldfile):
        """
        Returns a 2-tuple:
        0: bool signifying whether the image was successfully pre-warmed
        1: The url of the successfully created image OR the path on storage of
           the image that was not able to be successfully created.

        Arguments:
        `size_key_list`: A list of VersatileImageField size keys. Examples:
            * 'crop__800x450'
            * 'thumbnail__800x800'
        `versatileimagefieldfile`: A VersatileImageFieldFile instance
        """
        versatileimagefieldfile.create_on_demand = True
        try:
            url = get_url_from_image_key(versatileimagefieldfile, size_key)
        except Exception:
            success = False
            url_or_filepath = versatileimagefieldfile.name
            logger.exception('Thumbnail generation failed',
                             extra={'path': url_or_filepath})
        else:
            success = True
            url_or_filepath = url
        return (success, url_or_filepath)

    def warm(self):
        """
        Returns a 2-tuple:
        [0]: Number of images successfully pre-warmed
        [1]: A list of paths on the storage class associated with the
             VersatileImageField field being processed by `self` of
             files that could not be successfully seeded.
        """
        num_images_pre_warmed = 0
        failed_to_create_image_path_list = []
        total = self.queryset.count() * len(self.size_key_list)
        for a, instance in enumerate(self.queryset, start=1):
            for b, size_key in enumerate(self.size_key_list, start=1):
                success, url_or_filepath = self._prewarm_versatileimagefield(
                    size_key,
                    reduce(getattr, self.image_attr.split("."), instance)
                )
                if success is True:
                    num_images_pre_warmed += 1
                    if self.verbose:
                        cli_progress_bar(num_images_pre_warmed, total)
                else:
                    failed_to_create_image_path_list.append(url_or_filepath)

                if a * b == total:
                    stdout.write('\n')

        stdout.flush()
        return (num_images_pre_warmed, failed_to_create_image_path_list)

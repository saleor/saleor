from __future__ import unicode_literals

from django.conf import settings
from django.utils.encoding import python_2_unicode_compatible
from django.utils.six import iteritems

from ..settings import (
    cache,
    VERSATILEIMAGEFIELD_CACHE_LENGTH
)
from ..utils import get_filtered_path

from .base import ProcessedImage
from .mixins import DeleteAndClearCacheMixIn


class InvalidFilter(Exception):
    pass


@python_2_unicode_compatible
class FilteredImage(DeleteAndClearCacheMixIn, ProcessedImage):
    """
    A ProcessedImage subclass that applies a filter to an image.

    Constructor arguments:
        * `path_to_image`: The path within `storage` of the image
                           to filter.
        * `storage`: A django storage class.
        * `filename_key`: A string that is included in the filtered
                          filename to identify it. This should be short
                          and descriptive (i.e. 'grayscale' or 'invert')

    Subclasses must implement a process_image method.
    """

    def __init__(self, path_to_image, storage, create_on_demand, filename_key):
        super(FilteredImage, self).__init__(
            path_to_image, storage, create_on_demand
        )
        self.name = get_filtered_path(
            path_to_image=self.path_to_image,
            filename_key=filename_key,
            storage=storage
        )

        self.url = storage.url(self.name)

    def create_filtered_image(self, path_to_image, save_path_on_storage):
        """
        Creates a filtered image.
        `path_to_image`: The path to the image with the media directory
                         to resize.
        `save_path_on_storage`: Where on self.storage to save the filtered
                                image
        """

        image, file_ext, image_format, mime_type = self.retrieve_image(
            path_to_image
        )
        image, save_kwargs = self.preprocess(image, image_format)
        imagefile = self.process_image(image, image_format, save_kwargs)
        self.save_image(imagefile, save_path_on_storage, file_ext, mime_type)

    def __str__(self):
        return self.url


class DummyFilter(object):
    """
    A 'dummy' version of FilteredImage which is only used if
    settings.VERSATILEIMAGEFIELD_USE_PLACEHOLDIT is True
    """
    name = ''
    url = ''


class FilterLibrary(dict):
    """
    Exposes all filters registered with the sizedimageregistry
    (via sizedimageregistry.register_filter) to each VersatileImageField.

    Each filter also has access to each 'sizer' registered with
    sizedimageregistry (via sizedimageregistry.register_sizer)
    """

    def __init__(self, original_file_location,
                 storage, registry, ppoi, create_on_demand):
        self.original_file_location = original_file_location
        self.storage = storage
        self.registry = registry
        self.ppoi = ppoi
        self.create_on_demand = create_on_demand

    def __getattr__(self, key):
        return self[key]

    def __getitem__(self, key):
        """
        Returns a FilteredImage instance built from the FilteredImage subclass
        associated with self.registry[key]

        If no FilteredImage subclass is associated with self.registry[key],
        InvalidFilter will raise.
        """
        try:
            # FilteredImage instances are not built until they're accessed for
            # the first time (in order to cut down on memory usage and disk
            # space) However, once built, they can be accessed directly by
            # calling the dict superclass's __getitem__ (which avoids the
            # infinite loop that would be caused by using self[key]
            # or self.get(key))
            prepped_filter = dict.__getitem__(self, key)
        except KeyError:
            # See if `key` is associated with a valid filter.
            if key not in self.registry._filter_registry:
                raise InvalidFilter('`%s` is an invalid filter.' % key)
            else:
                # Handling 'empty' fields.
                if not self.original_file_location and getattr(
                    settings, 'VERSATILEIMAGEFIELD_USE_PLACEHOLDIT', False
                ):
                    # If VERSATILEIMAGEFIELD_USE_PLACEHOLDIT is True (i.e.
                    # settings.VERSATILEIMAGEFIELD_PLACEHOLDER_IMAGE is unset)
                    # use DummyFilter (so sized renditions can still return
                    # valid http://placehold.it URLs).
                    filtered_path = None
                    prepped_filter = DummyFilter()
                else:
                    filtered_path = get_filtered_path(
                        path_to_image=self.original_file_location,
                        filename_key=key,
                        storage=self.storage
                    )

                    filtered_url = self.storage.url(filtered_path)

                    filter_cls = self.registry._filter_registry[key]
                    prepped_filter = filter_cls(
                        path_to_image=self.original_file_location,
                        storage=self.storage,
                        create_on_demand=self.create_on_demand,
                        filename_key=key
                    )
                    if self.create_on_demand is True:
                        if cache.get(filtered_url):
                            # The filtered_url exists in the cache so the image
                            # already exists. So we `pass` to skip directly to
                            # the return statement.
                            pass
                        else:
                            if not self.storage.exists(filtered_path):
                                prepped_filter.create_filtered_image(
                                    path_to_image=self.original_file_location,
                                    save_path_on_storage=filtered_path
                                )

                            # Setting a super-long cache for the newly created
                            # image
                            cache.set(
                                filtered_url,
                                1,
                                VERSATILEIMAGEFIELD_CACHE_LENGTH
                            )

                # 'Bolting' all image sizers within
                # `self.registry._sizedimage_registry` onto
                # the prepped_filter instance
                for (
                        attr_name, sizedimage_cls
                ) in iteritems(self.registry._sizedimage_registry):
                    setattr(
                        prepped_filter,
                        attr_name,
                        sizedimage_cls(
                            path_to_image=filtered_path,
                            storage=self.storage,
                            create_on_demand=self.create_on_demand,
                            ppoi=self.ppoi
                        )
                    )
                # Assigning `prepped_filter` to `key` so future access
                # is fast/cheap
                self[key] = prepped_filter

        return dict.__getitem__(self, key)

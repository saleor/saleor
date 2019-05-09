"""Registry."""
from __future__ import unicode_literals

import copy

from .datastructures import FilteredImage, SizedImage


class AlreadyRegistered(Exception):
    """Already registered exception."""

    pass


class InvalidSizedImageSubclass(Exception):
    """Ivalid sized image subclass exception."""

    pass


class InvalidFilteredImageSubclass(Exception):
    """Invalid filtered image subclass exception."""

    pass


class NotRegistered(Exception):
    """Not registered sizer/filter exception."""

    pass


class UnallowedSizerName(Exception):
    """Unallowed sizer name exception."""

    pass


class UnallowedFilterName(Exception):
    """Unallowed filter name exception."""

    pass


class VersatileImageFieldRegistry(object):
    """
    A VersatileImageFieldRegistry object.

    Allows new SizedImage & FilteredImage subclasses to be dynamically added
    to all SizedImageFileField instances at runtime. New SizedImage subclasses
    are registered with the register_sizer method. New ProcessedImage
    subclasses are registered with the register_filter method.
    """

    unallowed_sizer_names = (
        'build_filters_and_sizers',
        'chunks',
        'close',
        'closed',
        'create_on_demand',
        'delete',
        'encoding',
        'field',
        'file',
        'fileno',
        'filters',
        'flush',
        'get_filtered_root_folder',
        'get_sized_root_folder',
        'get_filtered_sized_root_folder',
        'delete_matching_files_from_storage',
        'delete_filtered_images',
        'delete_sized_images',
        'delete_filtered_sized_images',
        'delete_all_created_images',
        'height',
        'instance',
        'isatty',
        'multiple_chunks',
        'name',
        'newlines',
        'open',
        'path',
        'ppoi',
        'read',
        'readinto',
        'readline',
        'readlines',
        'save',
        'seek',
        'size',
        'softspace',
        'storage',
        'tell',
        'truncate',
        'url',
        'validate_ppoi',
        'width',
        'write',
        'writelines',
        'xreadlines'
    )

    def __init__(self, name='versatileimage_registry'):
        """Initialize a registry."""
        self._sizedimage_registry = {}  # attr_name -> sizedimage_cls
        self._filter_registry = {}  # attr_name -> filter_cls
        self.name = name

    def register_sizer(self, attr_name, sizedimage_cls):
        """
        Register a new SizedImage subclass (`sizedimage_cls`).

        To be used via the attribute (`attr_name`).
        """
        if attr_name.startswith(
            '_'
        ) or attr_name in self.unallowed_sizer_names:
            raise UnallowedSizerName(
                "`%s` is an unallowed Sizer name. Sizer names cannot begin "
                "with an underscore or be named any of the "
                "following: %s." % (
                    attr_name,
                    ', '.join([
                        name
                        for name in self.unallowed_sizer_names
                    ])
                )
            )
        if not issubclass(sizedimage_cls, SizedImage):
            raise InvalidSizedImageSubclass(
                'Only subclasses of versatileimagefield.datastructures.'
                'SizedImage may be registered with register_sizer'
            )

        if attr_name in self._sizedimage_registry:
            raise AlreadyRegistered(
                'A SizedImage class is already registered to the `%s` '
                'attribute. If you would like to override this attribute, '
                'use the unregister method' % attr_name
            )
        else:
            self._sizedimage_registry[attr_name] = sizedimage_cls

    def unregister_sizer(self, attr_name):
        """
        Unregister the SizedImage subclass currently assigned to `attr_name`.

        If a SizedImage subclass isn't already registered to `attr_name`
        NotRegistered will raise.
        """
        if attr_name not in self._sizedimage_registry:
            raise NotRegistered(
                'No SizedImage subclass is registered to %s' % attr_name
            )
        else:
            del self._sizedimage_registry[attr_name]

    def register_filter(self, attr_name, filterimage_cls):
        """
        Register a new FilteredImage subclass (`filterimage_cls`).

        To be used via the attribute (filters.`attr_name`)
        """
        if attr_name.startswith('_'):
            raise UnallowedFilterName(
                '`%s` is an unallowed Filter name. Filter names cannot begin '
                'with an underscore.' % attr_name
            )
        if not issubclass(filterimage_cls, FilteredImage):
            raise InvalidFilteredImageSubclass(
                'Only subclasses of FilteredImage may be registered as '
                'filters with VersatileImageFieldRegistry'
            )

        if attr_name in self._filter_registry:
            raise AlreadyRegistered(
                'A ProcessedImageMixIn class is already registered to the `%s`'
                ' attribute. If you would like to override this attribute, '
                'use the unregister method' % attr_name
            )
        else:
            self._filter_registry[attr_name] = filterimage_cls

    def unregister_filter(self, attr_name):
        """
        Unregister the FilteredImage subclass currently assigned to attr_name.

        If a FilteredImage subclass isn't already registered to filters.
        `attr_name` NotRegistered will raise.
        """
        if attr_name not in self._filter_registry:
            raise NotRegistered(
                'No FilteredImage subclass is registered to %s' % attr_name
            )
        else:
            del self._filter_registry[attr_name]


versatileimagefield_registry = VersatileImageFieldRegistry()


def autodiscover():
    """
    Discover versatileimagefield.py modules.

    Iterate over django.apps.get_app_configs() and discover
    versatileimagefield.py modules.
    """
    from importlib import import_module
    from django.apps import apps
    from django.utils.module_loading import module_has_submodule

    for app_config in apps.get_app_configs():
        # Attempt to import the app's module.

        try:
            before_import_sizedimage_registry = copy.copy(
                versatileimagefield_registry._sizedimage_registry
            )
            before_import_filter_registry = copy.copy(
                versatileimagefield_registry._filter_registry
            )
            import_module('%s.versatileimagefield' % app_config.name)
        except Exception:
            # Reset the versatileimagefield_registry to the state before the
            # last import as this import will have to reoccur on the next
            # request and this could raise NotRegistered and AlreadyRegistered
            # exceptions (see django ticket #8245).
            versatileimagefield_registry._sizedimage_registry = \
                before_import_sizedimage_registry
            versatileimagefield_registry._filter_registry = \
                before_import_filter_registry

            # Decide whether to bubble up this error. If the app just
            # doesn't have the module in question, we can ignore the error
            # attempting to import it, otherwise we want it to bubble up.
            if module_has_submodule(app_config.module, 'versatileimagefield'):
                raise

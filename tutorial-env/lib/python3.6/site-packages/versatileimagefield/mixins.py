"""versatileimagefield Field mixins."""
from __future__ import unicode_literals

import os
import re

from django.utils.six import iteritems

from .datastructures import FilterLibrary
from .registry import autodiscover, versatileimagefield_registry
from .settings import (
    cache,
    VERSATILEIMAGEFIELD_CREATE_ON_DEMAND,
    VERSATILEIMAGEFIELD_SIZED_DIRNAME,
    VERSATILEIMAGEFIELD_FILTERED_DIRNAME
)
from .validators import validate_ppoi

autodiscover()

filter_regex_snippet = r'__({registered_filters})__'.format(
    registered_filters='|'.join([
        key
        for key, filter_cls in iteritems(
            versatileimagefield_registry._filter_registry
        )
    ])
)
sizer_regex_snippet = r'-({registered_sizers})-(\d+)x(\d+)(?:-\d+)?'.format(
    registered_sizers='|'.join([
        sizer_cls.get_filename_key_regex()
        for key, sizer_cls in iteritems(
            versatileimagefield_registry._sizedimage_registry
        )
    ])
)
filter_regex = re.compile(filter_regex_snippet + '$')
sizer_regex = re.compile(sizer_regex_snippet + '$')
filter_and_sizer_regex = re.compile(
    filter_regex_snippet + sizer_regex_snippet + '$'
)


class VersatileImageMixIn(object):
    """A mix-in that provides the filtering/sizing API."""

    def __init__(self, *args, **kwargs):
        """Construct PPOI and create_on_demand."""
        self._create_on_demand = VERSATILEIMAGEFIELD_CREATE_ON_DEMAND
        super(VersatileImageMixIn, self).__init__(*args, **kwargs)
        # Setting initial ppoi
        if self.field.ppoi_field:
            instance_ppoi_value = getattr(
                self.instance,
                self.field.ppoi_field,
                (0.5, 0.5)
            )
            self.ppoi = instance_ppoi_value
        else:
            self.ppoi = (0.5, 0.5)

    @property
    def url(self):
        """
        Return the appropriate URL.

        URL is constructed based on these field conditions:
            * If empty (not `self.name`) and a placeholder is defined, the
              URL to the placeholder is returned.
            * Otherwise, defaults to vanilla ImageFieldFile behavior.
        """
        if not self.name and self.field.placeholder_image_name:
            return self.storage.url(self.field.placeholder_image_name)

        return super(VersatileImageMixIn, self).url

    @property
    def create_on_demand(self):
        """create_on_demand getter."""
        return self._create_on_demand

    @create_on_demand.setter
    def create_on_demand(self, value):
        if not isinstance(value, bool):
            raise ValueError(
                "`create_on_demand` must be a boolean"
            )
        else:
            self._create_on_demand = value
            self.build_filters_and_sizers(self.ppoi, value)

    @property
    def ppoi(self):
        """Primary Point of Interest (ppoi) getter."""
        return self._ppoi_value

    @ppoi.setter
    def ppoi(self, value):
        """Primary Point of Interest (ppoi) setter."""
        ppoi = validate_ppoi(
            value,
            return_converted_tuple=True
        )
        if ppoi is not False:
            self._ppoi_value = ppoi
            self.build_filters_and_sizers(ppoi, self.create_on_demand)

    def build_filters_and_sizers(self, ppoi_value, create_on_demand):
        """Build the filters and sizers for a field."""
        name = self.name
        if not name and self.field.placeholder_image_name:
            name = self.field.placeholder_image_name
        self.filters = FilterLibrary(
            name,
            self.storage,
            versatileimagefield_registry,
            ppoi_value,
            create_on_demand
        )
        for (
            attr_name,
            sizedimage_cls
        ) in iteritems(versatileimagefield_registry._sizedimage_registry):
            setattr(
                self,
                attr_name,
                sizedimage_cls(
                    path_to_image=name,
                    storage=self.storage,
                    create_on_demand=create_on_demand,
                    ppoi=ppoi_value
                )
            )

    def get_filtered_root_folder(self):
        """Return the location where filtered images are stored."""
        folder, filename = os.path.split(self.name)
        return os.path.join(folder, VERSATILEIMAGEFIELD_FILTERED_DIRNAME, '')

    def get_sized_root_folder(self):
        """Return the location where sized images are stored."""
        folder, filename = os.path.split(self.name)
        return os.path.join(VERSATILEIMAGEFIELD_SIZED_DIRNAME, folder, '')

    def get_filtered_sized_root_folder(self):
        """Return the location where filtered + sized images are stored."""
        sized_root_folder = self.get_sized_root_folder()
        return os.path.join(
            sized_root_folder,
            VERSATILEIMAGEFIELD_FILTERED_DIRNAME
        )

    def delete_matching_files_from_storage(self, root_folder, regex):
        """
        Delete files in `root_folder` which match `regex` before file ext.

        Example values:
            * root_folder = 'foo/'
            * self.name = 'bar.jpg'
            * regex = re.compile('-baz')

            Result:
                * foo/bar-baz.jpg <- Deleted
                * foo/bar-biz.jpg <- Not deleted
        """
        if not self.name:   # pragma: no cover
            return
        try:
            directory_list, file_list = self.storage.listdir(root_folder)
        except OSError:   # pragma: no cover
            pass
        else:
            folder, filename = os.path.split(self.name)
            basename, ext = os.path.splitext(filename)
            for f in file_list:
                if not f.startswith(basename) or not f.endswith(ext):   # pragma: no cover
                    continue
                tag = f[len(basename):-len(ext)]
                assert f == basename + tag + ext
                if regex.match(tag) is not None:
                    file_location = os.path.join(root_folder, f)
                    self.storage.delete(file_location)
                    cache.delete(
                        self.storage.url(file_location)
                    )
                    print(
                        "Deleted {file} (created from: {original})".format(
                            file=os.path.join(root_folder, f),
                            original=self.name
                        )
                    )

    def delete_filtered_images(self):
        """Delete all filtered images created from `self.name`."""
        self.delete_matching_files_from_storage(
            self.get_filtered_root_folder(),
            filter_regex
        )

    def delete_sized_images(self):
        """Delete all sized images created from `self.name`."""
        self.delete_matching_files_from_storage(
            self.get_sized_root_folder(),
            sizer_regex
        )

    def delete_filtered_sized_images(self):
        """Delete all filtered sized images created from `self.name`."""
        self.delete_matching_files_from_storage(
            self.get_filtered_sized_root_folder(),
            filter_and_sizer_regex
        )

    def delete_all_created_images(self):
        """Delete all images created from `self.name`."""
        self.delete_filtered_images()
        self.delete_sized_images()
        self.delete_filtered_sized_images()

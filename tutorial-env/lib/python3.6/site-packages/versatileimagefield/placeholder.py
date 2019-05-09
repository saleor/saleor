from __future__ import unicode_literals

import os

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

empty = object()


class PlaceholderImage(object):
    """
    A class for configuring images to be used as 'placeholders' for
    blank/empty VersatileImageField fields.
    """

    _image_data = empty

    def setup(self):
        if isinstance(self.file, ContentFile):
            image_data = self.file
        else:
            image_data = ContentFile(self.file.read(), name=self.name)
        self._image_data = image_data
        self.file.close()

    @property
    def image_data(self):
        if self._image_data is empty:
            self.setup()
        return self._image_data


class OnDiscPlaceholderImage(PlaceholderImage):
    """
    A placeholder image saved to the same disc as the running
    application.
    """

    def __init__(self, path):
        """
        `path` - An absolute path to an on-disc image.
        """
        self.path = path

    def setup(self):
        folder, name = os.path.split(self.path)
        with open(self.path, 'rb') as file:
            content_file = ContentFile(file.read(), name=name)
        self.file = content_file
        self.name = name
        super(OnDiscPlaceholderImage, self).setup()


class OnStoragePlaceholderImage(PlaceholderImage):
    """
    A placeholder saved to a storage class. Does not necessarily need to
    be on the same storage as the field it is associated with.
    """

    def __init__(self, path, storage=None):
        """
        `path` - A path on `storage` to an Image.
        `storage` - A django storage class.
        """
        self.path = path
        self.storage = storage

    def setup(self):
        storage = self.storage or default_storage
        file = storage.open(self.path)
        folder, name = os.path.split(self.path)
        self.file = file
        self.name = name
        super(OnStoragePlaceholderImage, self).setup()

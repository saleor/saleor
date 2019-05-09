from __future__ import unicode_literals

from django.core.files.base import File
from django.db.models.fields.files import (
    FieldFile,
    ImageFieldFile,
    ImageFileDescriptor
)
from django.utils import six

from .mixins import VersatileImageMixIn


class VersatileImageFieldFile(VersatileImageMixIn, ImageFieldFile):

    def __getstate__(self):
        # VersatileImageFieldFile needs access to its associated model field
        # and an instance it's attached to in order to work properly, but the
        # only necessary data to be pickled is the file's name itself.
        # Everything else will be restored later, by
        # VersatileImageFileDescriptor below.
        state = super(VersatileImageFieldFile, self).__getstate__()
        state['_create_on_demand'] = self._create_on_demand
        return state


class VersatileImageFileDescriptor(ImageFileDescriptor):

    def __set__(self, instance, value):
        previous_file = instance.__dict__.get(self.field.name)
        super(VersatileImageFileDescriptor, self).__set__(instance, value)

        # Updating ppoi_field on attribute set
        if previous_file is not None:
            self.field.update_dimension_fields(instance, force=True)
            self.field.update_ppoi_field(instance)

    def __get__(self, instance=None, owner=None):
        if instance is None:
            return self

        # This is slightly complicated, so worth an explanation.
        # instance.file`needs to ultimately return some instance of `File`,
        # probably a subclass. Additionally, this returned object needs to have
        # the VersatileImageFieldFile API so that users can easily do things
        # like instance.file.path & have that delegated to the file storage
        # engine. Easy enough if we're strict about assignment in __set__, but
        # if you peek below you can see that we're not. So depending on the
        # current value of the field we have to dynamically construct some
        # sort of "thing" to return.

        # The instance dict contains whatever was originally assigned
        # in __set__.
        file = instance.__dict__[self.field.name]

        # Call the placeholder procecess method on VersatileImageField.
        # (This was called inside the VersatileImageField __init__ before) Fixes #28
        self.field.process_placeholder_image()

        # If this value is a string (instance.file = "path/to/file") or None
        # then we simply wrap it with the appropriate attribute class according
        # to the file field. [This is FieldFile for FileFields and
        # ImageFieldFile for ImageFields and their subclasses, like this class;
        # it's also conceivable that user subclasses might also want to
        # subclass the attribute class]. This object understands how to convert
        # a path to a file, and also how to handle None.
        if isinstance(file, six.string_types) or file is None:
            attr = self.field.attr_class(
                instance=instance,
                field=self.field,
                name=file
            )
            # Check if this field has a ppoi_field assigned
            if attr.field.ppoi_field:
                # Pulling the current value of the ppoi_field...
                ppoi = instance.__dict__[attr.field.ppoi_field]
                # ...and assigning it to VersatileImageField instance
                attr.ppoi = ppoi

            instance.__dict__[self.field.name] = attr

        # Other types of files may be assigned as well, but they need to have
        # the FieldFile interface added to the. Thus, we wrap any other type of
        # File inside a FieldFile (well, the field's attr_class, which is
        # usually FieldFile).
        elif isinstance(file, File) and not isinstance(file, FieldFile):
            file_copy = self.field.attr_class(instance, self.field, file.name)
            file_copy.file = file
            file_copy._committed = False
            instance.__dict__[self.field.name] = file_copy

        # Finally, because of the (some would say boneheaded) way pickle works,
        # the underlying FieldFile might not actually itself have an associated
        # file. So we need to reset the details of the FieldFile in those cases
        elif isinstance(file, FieldFile) and not hasattr(file, 'field'):
            file.instance = instance
            file.field = self.field
            file.storage = self.field.storage

            if file.field.ppoi_field:
                ppoi = instance.__dict__[file.field.ppoi_field]
                file.ppoi = ppoi

        # That was fun, wasn't it?
        return instance.__dict__[self.field.name]

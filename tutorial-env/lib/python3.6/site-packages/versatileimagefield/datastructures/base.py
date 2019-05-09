"""Base datastructures for manipulated images."""
from __future__ import unicode_literals

from PIL import Image

from django.core.files.uploadedfile import InMemoryUploadedFile

from ..settings import QUAL, VERSATILEIMAGEFIELD_PROGRESSIVE_JPEG
from ..utils import get_image_metadata_from_file_ext

EXIF_ORIENTATION_KEY = 274


class ProcessedImage(object):
    """
    A base class for processing/saving different renditions of an image.

    Constructor arguments:
        * `path_to_image`: A path to a file within `storage`
        * `storage`: A django storage class
        * `create_on_demand`: A bool signifying whether new images should be
                              created on-demand.

    Subclasses must define the `process_image` method. see
    versatileimagefield.datastructures.filteredimage.FilteredImage and
    versatileimagefield.datastructures.sizedimage.SizedImage
    for examples.

    Includes a preprocessing API based on image format/file type. See
    the `preprocess` method for more specific information.
    """

    name = None
    url = None

    def __init__(self, path_to_image, storage, create_on_demand,
                 placeholder_image=None):
        """Construct a ProcessedImage."""
        self.path_to_image = path_to_image
        self.storage = storage
        self.create_on_demand = create_on_demand
        self.placeholder_image = placeholder_image

    def process_image(self, image, image_format, **kwargs):
        """
        Ensure NotImplemented is raised if not overloaded by subclasses.

        Arguments:
            * `image`: a PIL Image instance
            * `image_format`: str, a valid PIL format (i.e. 'JPEG' or 'GIF')

        Returns a BytesIO representation of the resized image.

        Subclasses MUST implement this method.
        """
        raise NotImplementedError(
            'Subclasses MUST provide a `process_image` method.'
        )

    def preprocess(self, image, image_format):
        """
        Preprocess an image.

        An API hook for image pre-processing. Calls any image format specific
        pre-processors (if defined). I.E. If `image_format` is 'JPEG', this
        method will look for a method named `preprocess_JPEG`, if found
        `image` will be passed to it.

        Arguments:
            * `image`: a PIL Image instance
            * `image_format`: str, a valid PIL format (i.e. 'JPEG' or 'GIF')

        Subclasses should return a 2-tuple:
            * [0]: A PIL Image instance.
            * [1]: A dictionary of additional keyword arguments to be used
                   when the instance is saved. If no additional keyword
                   arguments, return an empty dict ({}).
        """
        save_kwargs = {'format': image_format}

        # Ensuring image is properly rotated
        if hasattr(image, '_getexif'):
            exif_datadict = image._getexif()  # returns None if no EXIF data
            if exif_datadict is not None:
                exif = dict(exif_datadict.items())
                orientation = exif.get(EXIF_ORIENTATION_KEY, None)
                if orientation == 3:
                    image = image.transpose(Image.ROTATE_180)
                elif orientation == 6:
                    image = image.transpose(Image.ROTATE_270)
                elif orientation == 8:
                    image = image.transpose(Image.ROTATE_90)

        # Ensure any embedded ICC profile is preserved
        save_kwargs['icc_profile'] = image.info.get('icc_profile')

        if hasattr(self, 'preprocess_%s' % image_format):
            image, addl_save_kwargs = getattr(
                self,
                'preprocess_%s' % image_format
            )(image=image)
            save_kwargs.update(addl_save_kwargs)

        return image, save_kwargs

    def preprocess_GIF(self, image, **kwargs):
        """
        Receive a PIL Image instance of a GIF and return 2-tuple.

        Args:
            * [0]: Original Image instance (passed to `image`)
            * [1]: Dict with a transparency key (to GIF transparency layer)
        """
        if 'transparency' in image.info:
            save_kwargs = {'transparency': image.info['transparency']}
        else:
            save_kwargs = {}
        return (image, save_kwargs)

    def preprocess_JPEG(self, image, **kwargs):
        """
        Receive a PIL Image instance of a JPEG and returns 2-tuple.

        Args:
            * [0]: Image instance, converted to RGB
            * [1]: Dict with a quality key (mapped to the value of `QUAL` as
                   defined by the `VERSATILEIMAGEFIELD_JPEG_RESIZE_QUALITY`
                   setting)
        """
        save_kwargs = {
            'progressive': VERSATILEIMAGEFIELD_PROGRESSIVE_JPEG,
            'quality': QUAL
        }
        if image.mode != 'RGB':
            image = image.convert('RGB')
        return (image, save_kwargs)

    def retrieve_image(self, path_to_image):
        """Return a PIL Image instance stored at `path_to_image`."""
        image = self.storage.open(path_to_image, 'rb')
        file_ext = path_to_image.rsplit('.')[-1]
        image_format, mime_type = get_image_metadata_from_file_ext(file_ext)

        return (
            Image.open(image),
            file_ext,
            image_format,
            mime_type
        )

    def save_image(self, imagefile, save_path, file_ext, mime_type):
        """
        Save an image to self.storage at `save_path`.

        Arguments:
            `imagefile`: Raw image data, typically a BytesIO instance.
            `save_path`: The path within self.storage where the image should
                         be saved.
            `file_ext`: The file extension of the image-to-be-saved.
            `mime_type`: A valid image mime type (as found in
                         versatileimagefield.utils)
        """
        file_to_save = InMemoryUploadedFile(
            imagefile,
            None,
            'foo.%s' % file_ext,
            mime_type,
            imagefile.tell(),
            None
        )
        file_to_save.seek(0)
        self.storage.save(save_path, file_to_save)

from io import BytesIO
from typing import Optional

import magic
from django.core.files.storage import default_storage
from PIL import Image

from . import MIME_TYPE_TO_PIL_IDENTIFIER, THUMBNAIL_SIZES

# from django.core.files.uploadedfile import InMemoryUploadedFile


def get_thumbnail_size(size: str) -> int:
    """Return the closest size to the given one of the available sizes."""
    size = int(size)
    if size in THUMBNAIL_SIZES:
        return size

    return min(THUMBNAIL_SIZES, key=lambda x: abs(x - size))


def prepare_thumbnail_file_name(
    file_name: str, size: int, format: Optional[str]
) -> str:
    file_path, file_ext = file_name.rsplit(".")
    file_ext = format or file_ext
    return file_path + f"_thumbnail_{size}." + file_ext


class ProcessedImage:
    EXIF_ORIENTATION_KEY = 274
    # Whether to create progressive JPEGs. Read more about progressive JPEGs
    # here: https://optimus.io/support/progressive-jpeg/
    PROGRESSIVE_JPEG = False
    # If true, instructs the WebP writer to use lossless compression.
    # https://pillow.readthedocs.io/en/latest/handbook/image-file-formats.html#webp
    # Defaults to False
    LOSSLESS_WEBP = False
    # The save quality of modified JPEG images. More info here:
    # https://pillow.readthedocs.io/en/latest/handbook/image-file-formats.html#jpeg
    JPEG_QUAL = 70
    # The save quality of modified WEBP images. More info here:
    # https://pillow.readthedocs.io/en/latest/handbook/image-file-formats.html#webp
    WEBP_QUAL = 70

    def __init__(
        self,
        image_path: str,
        size: int,
        format: Optional[str] = None,
        storage=default_storage,
    ):
        self.image_path = image_path
        self.size = size
        self.format = format
        self.storage = storage

    def create_thumbnail(self):
        image, image_format = self.retrieve_image()
        image, save_kwargs = self.preprocess(image, image_format)
        image_file = self.process_image(
            image=image,
            save_kwargs=save_kwargs,
        )
        return image_file

    def retrieve_image(self):
        """Return a PIL Image instance stored at `image_path`."""
        image = self.storage.open(self.image_path, "rb")
        image_format = self.get_image_metadata_from_file(image)
        return (Image.open(image), image_format)

    def get_image_metadata_from_file(self, file_like):
        """Return a image format and InMemoryUploadedFile-friendly save format.

        Receive a valid image file and returns a 2-tuple of two strings:
            [0]: Image format (i.e. 'jpg', 'gif' or 'png')
            [1]: InMemoryUploadedFile-friendly save format (i.e. 'image/jpeg')
        image_format, in_memory_file_type
        """
        mime_type = magic.from_buffer(file_like.read(1024), mime=True)
        file_like.seek(0)
        image_format = MIME_TYPE_TO_PIL_IDENTIFIER[mime_type]
        return image_format

    def preprocess(self, image, image_format):
        """Preprocess an image.

        An API hook for image pre-processing. Calls any image format specific
        pre-processors (if defined). I.E. If `image_format` is 'JPEG', this
        method will look for a method named `preprocess_JPEG`, if found
        `image` will be passed to it.

        Arguments:
            image: a PIL Image instance
            image_format: str, a valid PIL format (i.e. 'JPEG' or 'WEBP')

        Subclasses should return a 2-tuple:
            * [0]: A PIL Image instance.
            * [1]: A dictionary of additional keyword arguments to be used
                    when the instance is saved. If no additional keyword
                    arguments, return an empty dict ({}).

        """
        format = self.format or image_format
        save_kwargs = {"format": format}

        # Ensuring image is properly rotated
        if hasattr(image, "_getexif"):
            exif_datadict = image._getexif()  # returns None if no EXIF data
            if exif_datadict is not None:
                exif = dict(exif_datadict.items())
                orientation = exif.get(self.EXIF_ORIENTATION_KEY, None)
                if orientation == 3:
                    image = image.transpose(Image.ROTATE_180)
                elif orientation == 6:
                    image = image.transpose(Image.ROTATE_270)
                elif orientation == 8:
                    image = image.transpose(Image.ROTATE_90)

        # Ensure any embedded ICC profile is preserved
        save_kwargs["icc_profile"] = image.info.get("icc_profile")

        if hasattr(self, "preprocess_%s" % format):
            image, addl_save_kwargs = getattr(self, "preprocess_%s" % format)(
                image=image
            )
            save_kwargs.update(addl_save_kwargs)

        return image, save_kwargs

    def preprocess_GIF(self, image, **kwargs):
        """Receive a PIL Image instance of a GIF and return 2-tuple.

        Args:
            image: Original Image instance (passed to `image`)
            kwargs: Dict with a transparency key (to GIF transparency layer)

        """
        if "transparency" in image.info:
            save_kwargs = {"transparency": image.info["transparency"]}
        else:
            save_kwargs = {}
        return (image, save_kwargs)

    def preprocess_JPEG(self, image, **kwargs):
        """Receive a PIL Image instance of a JPEG and returns 2-tuple.

        Args:
            image: Image instance, converted to RGB
            kwargs: Dict with a quality key (mapped to the value of `JPEG_QUAL`
                    defined by the `VERSATILEIMAGEFIELD_JPEG_RESIZE_QUALITY`
                    setting)

        """
        save_kwargs = {"progressive": self.PROGRESSIVE_JPEG, "quality": self.JPEG_QUAL}
        if image.mode != "RGB":
            image = image.convert("RGB")
        return (image, save_kwargs)

    def preprocess_WEBP(self, image, **kwargs):
        """Receive a PIL Image instance of a WEBP and return 2-tuple.

        Args:
            image: Original Image instance (passed to `image`)
            kwargs: Dict with a quality key (mapped to the value of `WEBP_QUAL`
                    as defined by the `VERSATILEIMAGEFIELD_RESIZE_QUALITY`
                    setting)

        """
        save_kwargs = {
            "quality": self.WEBP_QUAL,
            "lossless": self.LOSSLESS_WEBP,
            "icc_profile": image.info.get("icc_profile", ""),
        }

        return (image, save_kwargs)

    def process_image(self, image, save_kwargs):
        """Return a BytesIO instance of `image` that fits in a bounding box.

        Bounding box dimensions are `width`x`height`.
        """
        image_file = BytesIO()
        image.thumbnail(
            (self.size, self.size),
        )
        image.save(image_file, **save_kwargs)
        return image_file

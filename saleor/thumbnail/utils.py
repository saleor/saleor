import os
import secrets
from io import BytesIO
from typing import TYPE_CHECKING, Optional

import graphene
import magic
from django.core.files import File
from django.core.files.storage import default_storage
from django.urls import reverse
from PIL import Image

from . import (
    DEFAULT_THUMBNAIL_SIZE,
    FILE_NAME_MAX_LENGTH,
    MIME_TYPE_TO_PIL_IDENTIFIER,
    THUMBNAIL_SIZES,
    IconThumbnailFormat,
    ThumbnailFormat,
)

if TYPE_CHECKING:
    from .models import Thumbnail


def get_image_or_proxy_url(
    thumbnail: Optional["Thumbnail"],
    instance_id: str,
    object_type: str,
    size: int,
    format: str | None,
):
    """Return the thumbnail ULR if thumbnails is provided, otherwise the proxy url."""
    return (
        prepare_image_proxy_url(instance_id, object_type, size, format)
        if thumbnail is None
        else thumbnail.image.url
    )


def prepare_image_proxy_url(
    instance_pk: str, object_type: str, size: int, format: str | None
):
    instance_id = graphene.Node.to_global_id(object_type, instance_pk)
    kwargs = {"instance_id": instance_id, "size": size}
    if format and format.lower() != ThumbnailFormat.ORIGINAL:
        kwargs["format"] = format.lower()
    return reverse("thumbnail", kwargs=kwargs)


def get_thumbnail_size(size: int | None) -> int:
    """Return the closest size to the given one of the available sizes."""
    if size is None:
        requested_size = DEFAULT_THUMBNAIL_SIZE
    else:
        requested_size = size
    if requested_size in THUMBNAIL_SIZES:
        return requested_size

    return min(THUMBNAIL_SIZES, key=lambda x: abs(x - requested_size))


def get_thumbnail_format(format: str | None) -> str | None:
    """Return the thumbnail format if it's supported, otherwise None."""
    if format is None:
        return None

    format = format.lower()
    if format == ThumbnailFormat.ORIGINAL:
        return None

    return format


def get_icon_thumbnail_format(format: str | None) -> str | None:
    """Return the icon thumbnail format if it's supported, otherwise None."""
    if not format or format.lower() == IconThumbnailFormat.ORIGINAL:
        return None
    return format


def prepare_thumbnail_file_name(file_name: str, size: int, format: str | None) -> str:
    file_path, file_ext = file_name.rsplit(".", 1)
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
    AVIF_QUAL = 70

    def __init__(
        self,
        image_source: str | File,
        size: int,
        format: str | None = None,
        storage=default_storage,
    ):
        self.image_source = image_source
        self.size = size
        self.format = format.upper() if format else None
        self.storage = storage

    def create_thumbnail(self):
        image, image_format = self.retrieve_image()
        image, save_kwargs = self.preprocess(image, image_format)
        image_file, thumbnail_format = self.process_image(
            image=image,
            save_kwargs=save_kwargs,
        )
        return image_file, thumbnail_format

    def retrieve_image(self):
        """Return a PIL Image instance stored at `image_source`."""
        image = self.image_source
        if isinstance(self.image_source, str):
            image = self.storage.open(self.image_source, "rb")
        image_format = self.get_image_metadata_from_file(image)
        return (Image.open(image), image_format)

    @classmethod
    def get_image_metadata_from_file(cls, file_like):
        """Return a image format and InMemoryUploadedFile-friendly save format.

        Receive a valid image file and returns a 2-tuple of two strings:
            [0]: Image format (i.e. 'jpg', 'gif' or 'png')
            [1]: InMemoryUploadedFile-friendly save format (i.e. 'image/jpeg')
        image_format, in_memory_file_type
        """
        mime_type = magic.from_buffer(file_like.read(1024), mime=True)
        file_like.seek(0)
        if mime_type not in MIME_TYPE_TO_PIL_IDENTIFIER:
            raise ValueError(f"Unsupported image MIME type: {mime_type}")
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
            try:
                # validation of the exif data was added in separate PR:
                # https://github.com/saleor/saleor/pull/11224, it means that there is a
                # possibility that we could have the file with corrupted exif data.
                # exif data is only used to apply some optional action on the image,
                # but without it, we are still able to create a thumbnail.
                exif_datadict = image._getexif()  # returns None if no EXIF data
            except SyntaxError:
                exif_datadict = None

            if exif_datadict is not None:
                exif = dict(exif_datadict.items())
                orientation = exif.get(self.EXIF_ORIENTATION_KEY, None)
                if orientation == 3:
                    image = image.transpose(Image.Transpose.ROTATE_180)
                elif orientation == 6:
                    image = image.transpose(Image.Transpose.ROTATE_270)
                elif orientation == 8:
                    image = image.transpose(Image.Transpose.ROTATE_90)

        # Ensure any embedded ICC profile is preserved
        save_kwargs["icc_profile"] = image.info.get("icc_profile")

        if hasattr(self, f"preprocess_{format}"):
            image, addl_save_kwargs = getattr(self, f"preprocess_{format}")(image=image)
            save_kwargs.update(addl_save_kwargs)

        return image, save_kwargs

    def preprocess_AVIF(self, image):
        """Receive a PIL Image instance of an AVIF and return 2-tuple."""
        save_kwargs = {
            "quality": self.AVIF_QUAL,
            "icc_profile": image.info.get("icc_profile", ""),
        }

        return (image, save_kwargs)

    def preprocess_GIF(self, image):
        """Receive a PIL Image instance of a GIF and return 2-tuple."""
        if "transparency" in image.info:
            save_kwargs = {"transparency": image.info["transparency"]}
        else:
            save_kwargs = {}
        return (image, save_kwargs)

    def preprocess_JPEG(self, image):
        """Receive a PIL Image instance of a JPEG and returns 2-tuple."""
        save_kwargs = {"progressive": self.PROGRESSIVE_JPEG, "quality": self.JPEG_QUAL}
        if image.mode != "RGB":
            image = image.convert("RGB")
        return (image, save_kwargs)

    def preprocess_WEBP(self, image):
        """Receive a PIL Image instance of a WEBP and return 2-tuple."""
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
        image_file.seek(0)
        return image_file, save_kwargs["format"]


class ProcessedIconImage(ProcessedImage):
    LOSSLESS_WEBP = True


def get_filename_from_url(url: str) -> str:
    """Prepare a unique filename for file from the URL to avoid overwriting."""
    file_name = os.path.basename(url)
    name, format = os.path.splitext(file_name)
    name = name[:FILE_NAME_MAX_LENGTH]
    hash = secrets.token_hex(nbytes=4)
    return f"{name}_{hash}{format}"

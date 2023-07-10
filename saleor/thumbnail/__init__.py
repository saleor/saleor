default_app_config = "saleor.thumbnail.app.ThumbnailAppConfig"

# defines the available thumbnail resolutions
THUMBNAIL_SIZES = [32, 64, 128, 256, 512, 1024, 2048, 4096]

DEFAULT_THUMBNAIL_SIZE = 4096

FILE_NAME_MAX_LENGTH = 55


class ThumbnailFormat:
    ORIGINAL = "original"
    AVIF = "avif"
    WEBP = "webp"

    CHOICES = [
        (ORIGINAL, "Original"),
        (AVIF, "AVIF"),
        (WEBP, "WebP"),
    ]


ALLOWED_THUMBNAIL_FORMATS = {ThumbnailFormat.AVIF, ThumbnailFormat.WEBP}

# PIL-supported file formats as found here:
# https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html
# Dict structure: {<mime-type>: <PIL-identifier>}
MIME_TYPE_TO_PIL_IDENTIFIER = {
    "image/avif": "AVIF",
    "image/bmp": "BMP",
    "image/dcx": "DCX",
    "image/eps": "EPS",
    "image/gif": "GIF",
    "image/jpeg": "JPEG",
    "image/pcd": "PCD",
    "image/pcx": "PCX",
    "image/png": "PNG",
    "image/x-ppm": "PPM",
    "image/psd": "PSD",
    "image/tiff": "TIFF",
    "image/x-xbitmap": "XBM",
    "image/x-xpm": "XPM",
    "image/webp": "WEBP",
}
PIL_IDENTIFIER_TO_MIME_TYPE = {v: k for k, v in MIME_TYPE_TO_PIL_IDENTIFIER.items()}


# Icon images
ICON_MIME_TYPES = ["image/png"]
MIN_ICON_SIZE = 256


class IconThumbnailFormat:
    """Thumbnail formats for icon images."""

    ORIGINAL = "original"
    WEBP = "webp"

    CHOICES = [
        (ORIGINAL, "Original"),
        (WEBP, "WebP"),
    ]


ALLOWED_ICON_THUMBNAIL_FORMATS = {IconThumbnailFormat.WEBP}

default_app_config = "saleor.thumbnail.app.ThumbnailAppConfig"

# defines the available thumbnail resolutions
THUMBNAIL_SIZES = [32, 64, 128, 256, 512, 1024, 2048, 4096]

DEFAULT_THUMBNAIL_SIZE = 4096


class ThumbnailFormat:
    ORIGINAL = "original"
    AVIF = "avif"
    WEBP = "webp"

    CHOICES = [
        (ORIGINAL, "Original"),
        (AVIF, "AVIF"),
        (WEBP, "WebP"),
    ]


# PIL-supported file formats as found here:
# https://infohost.nmt.edu/tcc/help/pubs/pil/formats.html
# {mime type: PIL Identifier}
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

# defines the available thumbnail resolutions
THUMBNAIL_SIZES = [32, 64, 128, 256, 512, 1024, 2048, 4096]


class ThumbnailFormat:
    # ORIGINAL = "original"
    WEBP = "webp"
    AVIF = "avif"

    CHOICES = [
        # (ORIGINAL, "original"),
        (WEBP, "WebP"),
        (AVIF, "AVIF"),
    ]

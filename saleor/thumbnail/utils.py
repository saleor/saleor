from . import THUMBNAIL_SIZES


def get_thumbnail_size(size: str):
    """Return the closest size to the given one of the available sizes."""
    if int(size) in THUMBNAIL_SIZES:
        return size

    return min(THUMBNAIL_SIZES, key=lambda x: abs(x - int(size)))

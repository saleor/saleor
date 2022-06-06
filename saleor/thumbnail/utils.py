import warnings

from . import THUMBNAIL_SIZES


def get_thumbnail_size(size):
    """Return the closest larger size if not more than 2 times larger.

    Otherwise, return the closest smaller size
    """
    if int(size) in THUMBNAIL_SIZES:
        return size
    avail_sizes = sorted(THUMBNAIL_SIZES)
    larger = [x for x in avail_sizes if size < x <= size * 2]
    smaller = [x for x in avail_sizes if x <= size]

    if larger:
        return larger[0]
    elif smaller:
        return smaller[-1]
    msg = (
        f"Thumbnail size {size} is not defined in settings "
        "and it won't be generated automatically"
    )
    warnings.warn(msg)
    return None

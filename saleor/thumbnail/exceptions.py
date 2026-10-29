class ImageTooLargeError(ValueError):
    """Raised when an image has more pixels than we are willing to decode.

    Subclasses `ValueError` so that callers already handling unusable images - the
    thumbnail view and `fetch_product_media_image_task` - treat it as an expected
    failure without needing to know about it.
    """

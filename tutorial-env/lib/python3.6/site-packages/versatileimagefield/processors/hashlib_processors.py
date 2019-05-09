import hashlib


def md5(image_key):
    """Return the md5 hash of image_key."""
    return hashlib.md5(image_key.encode('utf-8')).hexdigest()


def md5_16(image_key):
    """Return the first 16 characters of the md5 hash of image_key."""
    return md5(image_key)[:16]

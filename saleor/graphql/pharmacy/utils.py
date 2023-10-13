from django.conf import settings

from saleor.core.utils import build_absolute_uri


def build_file_uri(file_path):
    """Only supported for Wellstand GSC"""
    if not file_path:
        return ""

    if settings.GS_MEDIA_BUCKET_NAME:
        return f"{settings.GS_MEDIA_CUSTOM_ENDPOINT}/{settings.GS_LOCATION}/{file_path}"

    # Return regular save path
    return build_absolute_uri(f"{settings.MEDIA_URL}{file_path}")

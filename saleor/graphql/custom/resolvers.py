from django.core.exceptions import ValidationError

from saleor.custom.error_codes import CategoryCustomErrorCode
from saleor.custom.models import CategoryCustom


def check_slug_exists(slug):
    if CategoryCustom.objects.filter(slug=slug).exists():
        raise ValidationError(
            {
                "slug": ValidationError(
                    "Slug exists.",
                    code=CategoryCustomErrorCode.ALREADY_EXISTS,
                )
            }
        )

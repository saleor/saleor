from django.core.exceptions import ValidationError

from ....attribute import models
from ....attribute.error_codes import AttributeErrorCode


def validate_value_is_unique(attribute: models.Attribute, value: models.AttributeValue):
    """Check if the attribute value is unique within the attribute it belongs to."""
    duplicated_values = attribute.values.exclude(pk=value.pk).filter(slug=value.slug)
    if duplicated_values.exists():
        raise ValidationError(
            {
                "name": ValidationError(
                    f"Value with slug {value.slug} already exists.",
                    code=AttributeErrorCode.ALREADY_EXISTS.value,
                )
            }
        )

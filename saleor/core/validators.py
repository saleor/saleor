from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


def validate_empty_slug(value):
    if not value:
        raise ValidationError(
            _('The slug field cannot be empty.'),
            code='invalid_slug')

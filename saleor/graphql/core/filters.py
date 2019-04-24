import django_filters
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django_filters.fields import MultipleChoiceField


class DefaultMultipleChoiceField(MultipleChoiceField):
    default_error_messages = {
        "invalid_choice": _(
            "One of the specified IDs was invalid (%(value)s)."),
        "invalid_list": _("Enter a list of values."),
    }

    def to_python(self, value):
        if not value:
            return []
        return value

    def validate(self, value):
        """Validate that the input is a list or tuple."""
        if self.required and not value:
            raise ValidationError(
                self.error_messages['required'], code='required')
        if not isinstance(value, (list, tuple)):
            raise ValidationError(
                self.error_messages['invalid_list'], code='invalid_list')
        return True


class EnumFilter(django_filters.CharFilter):
    """ Filter class for graphene enum object.
    enum_class needs to be passed explicitly  as well as the method."""

    def __init__(self, input_class, *args, **kwargs):
        assert kwargs.get('method'), (
            'Providing exact filter method is required for EnumFilter')
        self.input_class = input_class
        super().__init__(*args, **kwargs)


class ListObjectTypeFilter(django_filters.MultipleChoiceFilter):
    field_class = DefaultMultipleChoiceField

    def __init__(self, input_class, *args, **kwargs):
        self.input_class = input_class
        super().__init__(*args, **kwargs)


class ObjectTypeFilter(django_filters.Filter):
    def __init__(self, input_class, *args, **kwargs):
        self.input_class = input_class
        super().__init__(*args, **kwargs)

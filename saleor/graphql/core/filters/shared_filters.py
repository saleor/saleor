from django.core.exceptions import ValidationError
from django.forms import CharField, Field, MultipleChoiceField
from django_filters import Filter, MultipleChoiceFilter
from graphql_relay import from_global_id


class GlobalIDFormField(Field):
    default_error_messages = {"invalid": "Invalid ID specified."}

    def clean(self, value):
        if not value and not self.required:
            return None

        try:
            _type, _id = from_global_id(value)
        except (TypeError, ValueError) as e:
            raise ValidationError(self.error_messages["invalid"]) from e

        try:
            CharField().clean(_id)
            CharField().clean(_type)
        except ValidationError as e:
            raise ValidationError(self.error_messages["invalid"]) from e

        return value


class GlobalIDFilter(Filter):
    field_class = GlobalIDFormField

    def filter(self, qs, value):
        """Convert the filter value to a primary key before filtering."""
        _id = None
        if value is not None:
            _, _id = from_global_id(value)
        return super().filter(qs, _id)


class GlobalIDMultipleChoiceField(MultipleChoiceField):
    default_error_messages = {
        "invalid_choice": "One of the specified IDs was invalid (%(value)s).",
        "invalid_list": "Enter a list of values.",
    }

    def to_python(self, value):
        return super().to_python(value)

    def valid_value(self, value):
        # Clean will raise a validation error if there is a problem
        GlobalIDFormField().clean(value)
        return True


class GlobalIDMultipleChoiceFilter(MultipleChoiceFilter):
    field_class = GlobalIDMultipleChoiceField

    def filter(self, qs, value):
        gids = [from_global_id(v)[1] for v in value]
        return super().filter(qs, gids)


def filter_metadata(qs, _, value):
    for metadata_item in value:
        metadata_value = metadata_item.get("value")
        metadata_key = metadata_item.get("key")
        if metadata_value:
            qs = qs.filter(metadata__contains={metadata_key: metadata_value})
        else:
            qs = qs.filter(metadata__has_key=metadata_key)
    return qs

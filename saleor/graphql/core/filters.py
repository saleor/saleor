import django_filters
import graphene
from django.core.exceptions import ValidationError
from django_filters.fields import MultipleChoiceField

from ..utils.filters import filter_range_field
from .enums import JobStatusEnum
from .types.common import DateTimeRangeInput


class DefaultMultipleChoiceField(MultipleChoiceField):
    default_error_messages = {"invalid_list": "Enter a list of values."}

    def to_python(self, value):
        if not value:
            return []
        if not isinstance(value, list):
            value = [value]
        return value

    def validate(self, value):
        """Validate that the input is a list or tuple."""
        if self.required and not value:
            raise ValidationError(self.error_messages["required"], code="required")
        if not isinstance(value, (list, tuple)):
            raise ValidationError(
                self.error_messages["invalid_list"], code="invalid_list"
            )
        return True


class EnumFilter(django_filters.CharFilter):
    """Filter class for Graphene enum object.

    enum_class needs to be passed explicitly as well as the method.
    """

    def __init__(self, input_class, *args, **kwargs):
        assert kwargs.get(
            "method"
        ), "Providing exact filter method is required for EnumFilter"
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


def filter_created_at(qs, _, value):
    return filter_range_field(qs, "created_at", value)


def filter_updated_at(qs, _, value):
    return filter_range_field(qs, "updated_at", value)


def filter_status(qs, _, value):
    if not value:
        return qs
    return qs.filter(status=value)


def filter_metadata(qs, _, value):
    for metadata_item in value:
        if metadata_item.value:
            qs = qs.filter(metadata__contains={metadata_item.key: metadata_item.value})
        else:
            qs = qs.filter(metadata__has_key=metadata_item.key)
    return qs


class BaseJobFilter(django_filters.FilterSet):
    created_at = ObjectTypeFilter(
        input_class=DateTimeRangeInput, method=filter_created_at
    )
    updated_at = ObjectTypeFilter(
        input_class=DateTimeRangeInput, method=filter_updated_at
    )
    status = EnumFilter(input_class=JobStatusEnum, method=filter_status)


class MetadataFilter(graphene.InputObjectType):
    key = graphene.String(required=True, description="Key of a metadata item.")
    value = graphene.String(required=False, description="Value of a metadata item.")


class MetadataFilterBase(django_filters.FilterSet):
    metadata = ListObjectTypeFilter(input_class=MetadataFilter, method=filter_metadata)

    class Meta:
        abstract = True

import django_filters
import graphene
from django.core.exceptions import ValidationError
from django.db import models
from django.forms import CharField, Field, MultipleChoiceField, NullBooleanField
from django_filters import Filter, MultipleChoiceFilter
from django_filters.filters import FilterMethod
from graphql_relay import from_global_id

from ..utils.filters import filter_range_field
from .enums import JobStatusEnum
from .types import DateTimeRangeInput


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


class DefaultOperationField(Field):
    def validate(self, value):
        if value and len(value) > 1:
            raise ValidationError("Only one option can be specified.", code="invalid")
        return super().validate(value)


class OperationObjectTypeFilter(django_filters.Filter):
    field_class = DefaultOperationField

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
        metadata_value = metadata_item.get("value")
        metadata_key = metadata_item.get("key")
        if metadata_value:
            qs = qs.filter(metadata__contains={metadata_key: metadata_value})
        else:
            qs = qs.filter(metadata__has_key=metadata_key)
    return qs


def filter_slug_list(qs, _, values):
    return qs.filter(slug__in=values)


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


class GlobalIDFormField(Field):
    default_error_messages = {"invalid": "Invalid ID specified."}

    def clean(self, value):
        if not value and not self.required:
            return None

        try:
            _type, _id = from_global_id(value)
        except (TypeError, ValueError):
            raise ValidationError(self.error_messages["invalid"])

        try:
            CharField().clean(_id)
            CharField().clean(_type)
        except ValidationError:
            raise ValidationError(self.error_messages["invalid"])

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


class WhereFilterSet(django_filters.FilterSet):
    """Implementation of FilterSet for where filtering.

    Should be used for all where FilterSet classes.
    """

    def filter_queryset(self, queryset):
        """Filter the queryset.

        Filter the queryset with the underlying form's `cleaned_data`. You must
        call `is_valid()` or `errors` before calling this method.

        This method should be overridden if additional filtering needs to be
        applied to the queryset before it is cached.
        """
        for name, value in self.form.cleaned_data.items():
            # Ensure that we not filter by fields that were not provided in the input.
            # The cleaned_data has all filter fields, but we only want to filter
            # by those that were specified in the query.
            if name not in self.form.data:
                continue
            queryset = self.filters[name].filter(queryset, value)
            assert isinstance(
                queryset, models.QuerySet
            ), f"Expected '{type(self).__name__}.{name}' to return a QuerySet, but got a {type(queryset).__name__} instead."
        return queryset


class MetadataWhereFilterBase(WhereFilterSet):
    metadata = ListObjectTypeFilter(input_class=MetadataFilter, method=filter_metadata)

    class Meta:
        abstract = True


class WhereFilter(Filter):
    def method():  # type: ignore
        # Filter method needs to be lazily resolved, as it may be dependent on
        # the 'parent' FilterSet.

        def fget(self):
            return self._method

        def fset(self, value):
            self._method = value

            # clear existing FilterMethod
            if isinstance(self.filter, WhereFilterMethod):
                del self.filter

            # override filter w/ FilterMethod.
            if value is not None:
                self.filter = WhereFilterMethod(self)

        return locals()

    method = property(**method())  # type: ignore

    def filter(self, qs, value):
        if self.distinct:
            qs = qs.distinct()
        lookup = f"{self.field_name}__{self.lookup_expr}"
        qs = self.get_method(qs)(**{lookup: value})
        return qs


class WhereFilterMethod(FilterMethod):
    def __call__(self, qs, value):
        """Override the default FilterMethod to allow filtering by empty values."""
        return self.method(qs, self.f.field_name, value)


class ObjectTypeWhereFilter(WhereFilter):
    def __init__(self, input_class, *args, **kwargs):
        self.input_class = input_class
        super().__init__(*args, **kwargs)


class OperationObjectTypeWhereFilter(WhereFilter):
    field_class = DefaultOperationField

    def __init__(self, input_class, *args, **kwargs):
        self.input_class = input_class
        super().__init__(*args, **kwargs)


class ListObjectTypeWhereFilter(MultipleChoiceFilter, WhereFilter):
    field_class = DefaultMultipleChoiceField

    def __init__(self, input_class, *args, **kwargs):
        self.input_class = input_class
        super().__init__(*args, **kwargs)


class BooleanWhereFilter(WhereFilter):
    field_class = NullBooleanField


class CharWhereFilter(WhereFilter):
    field_class = CharField


class EnumWhereFilter(CharWhereFilter):
    """Wheer filter class for Graphene enum object.

    enum_class needs to be passed explicitly as well as the method.
    """

    def __init__(self, input_class, *args, **kwargs):
        assert kwargs.get(
            "method"
        ), "Providing exact filter method is required for EnumFilter"
        self.input_class = input_class
        super().__init__(*args, **kwargs)


class GlobalIDMultipleChoiceWhereFilter(MultipleChoiceFilter, WhereFilter):
    field_class = GlobalIDMultipleChoiceField

    def filter(self, qs, value):
        gids = [from_global_id(v)[1] for v in value]
        return super().filter(qs, gids)


class GlobalIDWhereFilter(WhereFilter):
    field_class = GlobalIDFormField

    def filter(self, qs, value):
        """Convert the filter value to a primary key before filtering."""
        _id = None
        if value is not None:
            _, _id = from_global_id(value)
        return super(GlobalIDFilter, self).filter(qs, _id)  # type: ignore

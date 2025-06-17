import django_filters
from django.db import models
from django.forms import CharField, NullBooleanField
from django_filters import Filter, MultipleChoiceFilter
from django_filters.filters import FilterMethod
from graphql_relay import from_global_id

from .filters import (
    DefaultMultipleChoiceField,
    DefaultOperationField,
    ListObjectTypeFilter,
    MetadataFilter,
)
from .shared_filters import (
    GlobalIDFilter,
    GlobalIDFormField,
    GlobalIDMultipleChoiceField,
    filter_metadata,
)
from .where_input import MetadataFilterInput


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
            assert isinstance(queryset, models.QuerySet), (
                f"Expected '{type(self).__name__}.{name}' to return a QuerySet, but got a {type(queryset).__name__} instead."
            )
        return queryset


class WhereFilter(Filter):
    @property
    def method(self):
        # Filter method needs to be lazily resolved, as it may be dependent on
        # the 'parent' FilterSet.
        return self._method

    @method.setter
    def method(self, value):
        self._method = value

        # clear existing FilterMethod
        if isinstance(self.filter, WhereFilterMethod):
            del self.filter

        # override filter w/ FilterMethod.
        if value is not None:
            self.filter = WhereFilterMethod(self)  # type: ignore[method-assign]

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
    """Where filter class for Graphene enum object.

    enum_class needs to be passed explicitly as well as the method.
    """

    def __init__(self, input_class, *args, **kwargs):
        assert kwargs.get("method"), (
            "Providing exact filter method is required for EnumFilter"
        )
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
        return super(GlobalIDFilter, self).filter(qs, _id)  # type: ignore[misc]


class MetadataWhereFilterBase(WhereFilterSet):
    metadata = ListObjectTypeFilter(input_class=MetadataFilter, method=filter_metadata)

    class Meta:
        abstract = True


def filter_where_metadata(qs, _, value):
    """Filter queryset by metadata.

    We are allowing to filter metadata by:
    - Key existence: returns items where the specified key exists (when no value is provided)
    - Equals (`eq`): returns items where the key matches the given value
    - One of (`one_of`): returns items where the key matches any value in the provided list
    """
    if not value:
        return qs.none()
    key = value["key"]
    value_data = value.get("value")
    if not value_data:
        return qs.filter(metadata__has_key=key)
    if eq := value_data.get("eq"):
        return qs.filter(metadata__contains={key: eq})
    if one_of := value_data.get("one_of"):
        lookup = models.Q()
        for item in one_of:
            lookup |= models.Q(metadata__contains={key: item})
        return qs.filter(lookup)
    return qs.none()


class MetadataWhereBase(WhereFilterSet):
    metadata = ObjectTypeWhereFilter(
        input_class=MetadataFilterInput,
        method=filter_where_metadata,
        help_text="Filter by metadata fields.",
    )

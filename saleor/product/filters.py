import functools
import operator
from collections import OrderedDict, defaultdict
from itertools import chain
from typing import Dict, Iterable

from django.db.models import Q, QuerySet
from django.forms import CheckboxSelectMultiple
from django_filters import MultipleChoiceFilter, OrderingFilter, RangeFilter

from ..core.filters import SortedFilterSet
from .models import Attribute, Product

SORT_BY_FIELDS = OrderedDict(
    [
        ("name", "name"),
        ("minimal_variant_price_amount", "price"),
        ("updated_at", "last updated"),
    ]
)


T_PRODUCT_FILTER_QUERIES = Dict[int, Iterable[int]]


def filter_products_by_attributes_values(qs, queries: T_PRODUCT_FILTER_QUERIES):
    # Combine filters of the same attribute with OR operator
    # and then combine full query with AND operator.
    combine_and = [
        Q(**{"attributes__values__pk__in": values_pk})
        | Q(**{"variants__attributes__values__pk__in": values_pk})
        for _, values_pk in queries.items()
    ]
    query = functools.reduce(operator.and_, combine_and)
    qs = qs.filter(query).distinct()
    return qs


class AttributeValuesFilter(MultipleChoiceFilter):
    """A filter that is only there for rendering the attribute fields.

    The attributes will then be filtered in ``ProductFilter#filter_queryset``.

    This is a temporary work-around for: https://github.com/django/django/pull/8119
    """


class ProductFilter(SortedFilterSet):
    sort_by = OrderingFilter(
        label="Sort by", fields=SORT_BY_FIELDS.keys(), field_labels=SORT_BY_FIELDS,
    )
    minimal_variant_price = RangeFilter(
        label="Price", field_name="minimal_variant_price_amount",
    )

    class Meta:
        model = Product
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        attributes = self._get_attributes()
        filters = {}
        for attribute in attributes:
            filters[attribute.slug] = AttributeValuesFilter(
                label=attribute.translated.name,
                widget=CheckboxSelectMultiple,
                choices=self._get_attribute_choices(attribute),
            )
        self.filters.update(filters)

    def _get_attributes(self):
        q_product_attributes = self._get_product_attributes_lookup()
        q_variant_attributes = self._get_variant_attributes_lookup()
        product_attributes = (
            Attribute.objects.prefetch_related("translations", "values__translations")
            .exclude(filterable_in_storefront=False)
            .filter(q_product_attributes)
            .distinct()
        )
        variant_attributes = (
            Attribute.objects.prefetch_related("translations", "values__translations")
            .exclude(filterable_in_storefront=False)
            .filter(q_variant_attributes)
            .distinct()
        )

        attributes = chain(product_attributes, variant_attributes)
        attributes = sorted(
            attributes, key=lambda attr: attr.storefront_search_position
        )
        return attributes

    def _get_product_attributes_lookup(self):
        raise NotImplementedError()

    def _get_variant_attributes_lookup(self):
        raise NotImplementedError()

    def _get_attribute_choices(self, attribute):
        return [
            (choice.pk, choice.translated.name) for choice in attribute.values.all()
        ]

    def filter_queryset(self, queryset):
        """Temporary workaround for filtering products by their attributes values.

        Refer to https://code.djangoproject.com/ticket/25367.

        Filter the queryset with the underlying form's `cleaned_data`. You must
        call `is_valid()` or `errors` before calling this method.

        This method should be overridden if additional filtering needs to be
        applied to the queryset before it is cached.
        """

        attribute_values = defaultdict(set)
        for name, value in self.form.cleaned_data.items():
            filter_field = self.filters[name]
            if isinstance(filter_field, AttributeValuesFilter):
                value = {int(pk) for pk in value}
                if value:
                    attribute_values[name].update(value)
                continue

            # Imported from django_filters.filterset.BaseFilterSet#filter_queryset.
            queryset = filter_field.filter(queryset, value)
            assert isinstance(queryset, QuerySet), (
                "Expected '%s.%s' to return a QuerySet, but got a %s instead."
                % (type(self).__name__, name, type(queryset).__name__)
            )

        if attribute_values:
            queryset = filter_products_by_attributes_values(queryset, attribute_values)
        return queryset

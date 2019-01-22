import functools
import operator
from collections import OrderedDict

from django.db.models import Q
from django.forms import CheckboxSelectMultiple
from django.utils.translation import pgettext_lazy
from django_filters import MultipleChoiceFilter, OrderingFilter, RangeFilter

from ..core.filters import SortedFilterSet
from .models import Attribute, Product

SORT_BY_FIELDS = OrderedDict([
    ('name', pgettext_lazy('Product list sorting option', 'name')),
    ('price', pgettext_lazy('Product list sorting option', 'price')),
    ('updated_at', pgettext_lazy(
        'Product list sorting option', 'last updated'))])


class MergedAttributes:
    """Merge attribute queryset into a dictionary by attribute slug.
    Note that the attribute values should be prefetched for
    optimizing performance."""
    def __init__(self, attributes):
        self._merged_attributes = self._get_merged_attributes(attributes)

    def _get_merged_attributes(self, attributes):
        """Merge attributes with same slug into one item in dictionary."""
        merged_attributes = {}
        for attribute in attributes:
            same_slug_attrs = merged_attributes.setdefault(attribute.slug, [])
            same_slug_attrs.append(attribute)
        return merged_attributes

    def get_kvs(self, attr_slug, value_slug):
        """Get a list of attribute-pk/value-pk pairs
        for attributes with same attribute slug and value slug."""
        kvs = []
        for attr in self._merged_attributes[attr_slug]:
            for value in attr.values.all():
                if value_slug == value.slug:
                    kvs.append((attr.pk, value.pk))
        return kvs

    def get_attributes(self):
        """Get attributes as a dict."""
        return self._merged_attributes

    def get_values(self, attr_slug):
        """Get attributes values for attributes with same attribute slug."""
        values = dict()
        for attr in self._merged_attributes[attr_slug]:
            for value in attr.values.all():
                values.setdefault(value.slug, []).append(value)
        return values

    def get_choices(self, attr_slug):
        """Get attributes values as choices for MultipleChoiceFilter."""
        values, choices = self.get_values(attr_slug), []
        for value_slug, value_list in values.items():
            v = serialize_attribute((attr_slug, value_slug))
            # By default the translated name of the first one in
            # attribute values with same slug is used
            label = value_list[0].translated.name
            choices.append((v, label))
        return choices

    def _product_attr_or_product_variant_attr_query(self, attr_k, attr_v):
        product_attr_query = Q(**{'attributes__%s' % (attr_k, ): attr_v})
        variant_attr_query = Q(
            **{'variants__attributes__%s' % (attr_k, ): attr_v})
        return product_attr_query | variant_attr_query

    def get_query(self, attr_slug, value_slug):
        """Get query for attributes with same attribute slug and value slug."""
        # Validate attribute slug and value slug
        if attr_slug not in self.get_attributes():
            raise ValueError('Unknown attribute slug: %r' % (attr_slug,))
        if value_slug not in self.get_values(attr_slug):
            raise ValueError(
                'Unknown attribute value slug: %r' % (value_slug,))

        # Combine filters of attributes
        # with same attribute slug and value slug using OR operator
        kvs = self.get_kvs(attr_slug, value_slug)
        query = functools.reduce(
            operator.or_,
            [self._product_attr_or_product_variant_attr_query(
                attr_pk, value_pk) for attr_pk, value_pk in kvs])

        return query


class AttributeMultipleChoiceFilter(MultipleChoiceFilter):
    def __init__(self, merged_attributes, *args, **kwargs):
        self._merged_attributes = merged_attributes
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        """Copied from django-filter directly but only modified
        get_filter_predicate which supports returning query directly."""
        if not value:
            # Even though not a noop, no point filtering if empty.
            return qs

        if self.is_noop(qs, value):
            return qs

        if not self.conjoined:
            q = Q()
        for v in set(value):
            if v == self.null_value:
                v = None
            predicate = self.get_filter_predicate(v)
            if self.conjoined:
                qs = self.get_method(qs)(predicate)
            else:
                q |= Q(predicate)

        if not self.conjoined:
            qs = self.get_method(qs)(q)

        return qs.distinct() if self.distinct else qs

    def get_filter_predicate(self, v):
        # Parse attribute scalar
        attribute = parse_attribute(v)
        if attribute is None:
            raise ValueError(
                'Unknown attribute scalar: %r' % (attribute,))

        attr_slug, value_slug = attribute
        return self._merged_attributes.get_query(attr_slug, value_slug)


class ProductFilter(SortedFilterSet):
    sort_by = OrderingFilter(
        label=pgettext_lazy('Product list sorting form', 'Sort by'),
        fields=SORT_BY_FIELDS.keys(),
        field_labels=SORT_BY_FIELDS)
    price = RangeFilter(
        label=pgettext_lazy('Currency amount', 'Price'))

    class Meta:
        model = Product
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._merged_attributes = self._get_merged_attributes()
        self.filters.update(self._get_attributes_filters())
        self.filters = OrderedDict(sorted(self.filters.items()))

    def _get_merged_attributes(self):
        q_product_attributes = self._get_product_attributes_lookup()
        q_variant_attributes = self._get_variant_attributes_lookup()
        attributes = (
            Attribute.objects.all()
            .prefetch_related('translations', 'values__translations')
            .filter(q_product_attributes | q_variant_attributes)
            .distinct())

        merged_attributes = MergedAttributes(attributes)
        return merged_attributes

    def _get_product_attributes_lookup(self):
        raise NotImplementedError()

    def _get_variant_attributes_lookup(self):
        raise NotImplementedError()

    def _get_attributes_filters(self):
        filters, attributes = {}, self._merged_attributes.get_attributes()
        for attr_slug in attributes:
            filters[attr_slug] = AttributeMultipleChoiceFilter(
                merged_attributes=self._merged_attributes,
                # By default the translated name of the first one in
                # # attributes with same slug is used
                label=attributes[attr_slug][0].translated.name,
                widget=CheckboxSelectMultiple,
                choices=self._merged_attributes.get_choices(attr_slug))
        return filters


class ProductCategoryFilter(ProductFilter):
    def __init__(self, *args, **kwargs):
        self.category = kwargs.pop('category')
        super().__init__(*args, **kwargs)

    def _get_product_attributes_lookup(self):
        categories = self.category.get_descendants(include_self=True)
        return Q(product_type__products__category__in=categories)

    def _get_variant_attributes_lookup(self):
        categories = self.category.get_descendants(include_self=True)
        return Q(product_variant_type__products__category__in=categories)


class ProductCollectionFilter(ProductFilter):
    def __init__(self, *args, **kwargs):
        self.collection = kwargs.pop('collection')
        super().__init__(*args, **kwargs)

    def _get_product_attributes_lookup(self):
        return Q(product_type__products__collections=self.collection)

    def _get_variant_attributes_lookup(self):
        return Q(product_variant_type__products__collections=self.collection)

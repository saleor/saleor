from __future__ import unicode_literals
from collections import OrderedDict

from django_filters import (FilterSet, MultipleChoiceFilter, RangeFilter,
                            OrderingFilter)
from django.forms import CheckboxSelectMultiple
from django.utils.translation import pgettext_lazy

from django_prices.models import PriceField

from .models import Product

SORT_BY_FIELDS = (('price', pgettext_lazy('Sort by filter', 'price')),
                  ('name', pgettext_lazy('Sort by filter', 'name')))


class ProductFilter(FilterSet):
    def __init__(self, *args, **kwargs):
        super(ProductFilter, self).__init__(*args, **kwargs)
        product_attributes, variant_attributes = self._get_attributes()
        self._add_product_attributes_filters(product_attributes)
        self._add_product_variants_attributes_filters(variant_attributes)
        self.filters = OrderedDict(sorted(self.filters.items()))

    sort_by = OrderingFilter(
        label='Sort by',
        fields=SORT_BY_FIELDS
    )

    class Meta:
        model = Product
        fields = ['price']
        filter_overrides = {
            PriceField: {
                'filter_class': RangeFilter
            }
        }

    def _get_attributes(self):
        product_attributes = set()
        variant_attributes = set()
        for product in self.queryset:
            for attribute in product.product_class.variant_attributes.all():
                variant_attributes.add(attribute)
            for attribute in product.product_class.product_attributes.all():
                product_attributes.add(attribute)
        return product_attributes, variant_attributes

    def _add_product_attributes_filters(self, product_attributes):
        for attribute in product_attributes:
            self.filters[attribute.slug] = MultipleChoiceFilter(
                name='attributes__%s' % attribute.pk,
                label=attribute.name,
                widget=CheckboxSelectMultiple,
                choices=get_attribute_choices(attribute))

    def _add_product_variants_attributes_filters(self, variant_attributes):
        for attribute in variant_attributes:
            self.filters[attribute.slug] = MultipleChoiceFilter(
                name='variants__attributes__%s' % attribute.pk,
                label=attribute.name,
                widget=CheckboxSelectMultiple,
                choices=get_attribute_choices(attribute))


def get_attribute_choices(attribute):
    return [(choice.pk, choice.name) for choice in attribute.values.all()]

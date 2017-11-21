from __future__ import unicode_literals

from django_filters import (CharFilter, FilterSet, RangeFilter, OrderingFilter)
from django.utils.translation import pgettext_lazy
from django_prices.models import PriceField

from ...product.models import Category, Product


SORT_BY_FIELDS = {'name': pgettext_lazy('Product list sorting option', 'name'),
                  'price': pgettext_lazy(
                      'Product list sorting option', 'price')}


class ProductFilter(FilterSet):
    name = CharFilter(
        label=pgettext_lazy('Product list name filter', 'Name'),
        lookup_expr='icontains')
    sort_by = OrderingFilter(
        label=pgettext_lazy('Product list sorting filter', 'Sort by'),
        fields=SORT_BY_FIELDS.keys(),
        field_labels=SORT_BY_FIELDS)

    class Meta:
        model = Product
        fields = ['name', 'categories', 'is_published', 'is_featured', 'price']
        filter_overrides = {
            PriceField: {
                'filter_class': RangeFilter
            }
        }

    def get_chips(self):
        categories = Category.objects.all()
        chips = []
        for iterator, item in enumerate(self.form):
            if item.name is not 'sort_by' and item.value():
                label = item.label
                if isinstance(item.value(), (list, tuple)):
                    if item.name == 'price':
                        if any(item.value()):
                            chips.append(label + ': ' + ' - '.join(item.value()))
                    elif item.name == 'categories':
                        for value in item.value():
                            chips.append(
                                label + ': ' + categories.get(pk=value).name)
                    else:
                        for value in item.value():
                            chips.append(label + ': ' + str(value))
                else:
                    value = item.value()
                    chips.append(label + ': ' + str(value))
            else:
                continue
        return chips

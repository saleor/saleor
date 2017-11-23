from __future__ import unicode_literals

from django import forms
from django.utils.translation import pgettext_lazy
from django_filters import (
    CharFilter, ChoiceFilter, FilterSet, RangeFilter, OrderingFilter)
from django_prices.models import PriceField

from ...product.models import Product

SORT_BY_FIELDS = {'name': pgettext_lazy('Product list sorting option', 'name'),
                  'price': pgettext_lazy(
                      'Product list sorting option', 'price')}

PUBLISHED_CHOICES = (
    ('1', pgettext_lazy('Is publish filter choice', 'Published')),
    ('0', pgettext_lazy('Is publish filter choice', 'Not published')))

FEATURED_CHOICES = (
    ('1', pgettext_lazy('Is featured filter choice', 'Featured')),
    ('0', pgettext_lazy('Is featured filter choice', 'Not featured')))


class ProductFilter(FilterSet):
    name = CharFilter(
        label=pgettext_lazy('Product list name filter label', 'Name'),
        lookup_expr='icontains')
    sort_by = OrderingFilter(
        label=pgettext_lazy('Product list sorting filter label', 'Sort by'),
        fields=SORT_BY_FIELDS.keys(),
        field_labels=SORT_BY_FIELDS)
    is_published = ChoiceFilter(
        label=pgettext_lazy(
            'Product list is published filter label', 'Is published'),
        choices=PUBLISHED_CHOICES,
        empty_label=pgettext_lazy('Filter empty choice label', 'All'),
        widget=forms.Select)
    is_featured = ChoiceFilter(
        label=pgettext_lazy(
            'Product list is featured filter label', 'Is featured'),
        choices=FEATURED_CHOICES,
        empty_label=pgettext_lazy('Filter empty choice label', 'All'),
        widget=forms.Select)

    class Meta:
        model = Product
        fields = ['name', 'categories', 'is_published', 'is_featured', 'price']
        filter_overrides = {
            PriceField: {
                'filter_class': RangeFilter
            }
        }

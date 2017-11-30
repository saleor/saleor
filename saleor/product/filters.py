from __future__ import unicode_literals
from collections import OrderedDict

from django_filters import (FilterSet, MultipleChoiceFilter, RangeFilter,
                            OrderingFilter)
from django.forms import CheckboxSelectMultiple, ValidationError
from django.utils.translation import pgettext_lazy

from django_prices.models import PriceField

from .models import Product, ProductAttribute


SORT_BY_FIELDS = {'name': pgettext_lazy('Product list sorting option', 'name'),
                  'price': pgettext_lazy(
                      'Product list sorting option', 'price')}


class ProductFilter(FilterSet):
    def __init__(self, *args, **kwargs):
        self.category = kwargs.pop('category')
        super(ProductFilter, self).__init__(*args, **kwargs)
        self.product_attributes, self.variant_attributes = (
            self._get_attributes())
        self.filters.update(self._get_product_attributes_filters())
        self.filters.update(self._get_product_variants_attributes_filters())
        self.filters = OrderedDict(sorted(self.filters.items()))
        self.form.fields['sort_by'].validators.append(self.validate_sort_by)

    sort_by = OrderingFilter(
        label=pgettext_lazy('Product list sorting form', 'Sort by'),
        fields=SORT_BY_FIELDS.keys(),
        field_labels=SORT_BY_FIELDS
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
        product_attributes = (
            ProductAttribute.objects.all()
            .prefetch_related('values')
            .filter(products_class__products__categories=self.category)
            .distinct())
        variant_attributes = (
            ProductAttribute.objects.all()
            .prefetch_related('values')
            .filter(product_variants_class__products__categories=self.category)
            .distinct())
        return product_attributes, variant_attributes

    def _get_product_attributes_filters(self):
        filters = {}
        for attribute in self.product_attributes:
            filters[attribute.slug] = MultipleChoiceFilter(
                name='attributes__%s' % attribute.pk,
                label=attribute.name,
                widget=CheckboxSelectMultiple,
                choices=self._get_attribute_choices(attribute))
        return filters

    def _get_product_variants_attributes_filters(self):
        filters = {}
        for attribute in self.variant_attributes:
            filters[attribute.slug] = MultipleChoiceFilter(
                name='variants__attributes__%s' % attribute.pk,
                label=attribute.name,
                widget=CheckboxSelectMultiple,
                choices=self._get_attribute_choices(attribute))
        return filters

    def _get_attribute_choices(self, attribute):
        return [(choice.pk, choice.name) for choice in attribute.values.all()]

    def validate_sort_by(self, value):
        if value.strip('-') not in SORT_BY_FIELDS:
            raise ValidationError(
                _('%(value)s is not a valid sorting option'),
                params={'value': value}
            )

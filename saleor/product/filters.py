from __future__ import unicode_literals
from collections import OrderedDict
from copy import deepcopy

from django_filters import FilterSet, MultipleChoiceFilter, RangeFilter, \
    OrderingFilter
from django.forms import CheckboxSelectMultiple

from django_prices.models import PriceField

from .models import Product


class ProductFilter(FilterSet):
    def __init__(self, *args, **kwargs):
        super(ProductFilter, self).__init__(*args, **kwargs)
        product_attributes = set()
        variant_attributes = set()
        for product in self.queryset:
            for attribute in product.product_class.variant_attributes.all():
                variant_attributes.add(attribute)
            for attribute in product.product_class.product_attributes.all():
                product_attributes.add(attribute)

        for attribute in product_attributes:
            self.filters[attribute.slug] = MultipleChoiceFilter(
                name='attributes__%s' % attribute.pk,
                label=attribute.name,
                widget=CheckboxSelectMultiple,
                choices=get_attribute_choices(attribute))

        for attribute in variant_attributes:
            self.filters[attribute.slug] = MultipleChoiceFilter(
                name='variants__attributes__%s' % attribute.pk,
                label=attribute.name,
                widget=CheckboxSelectMultiple,
                choices=get_attribute_choices(attribute))
        self.filters = OrderedDict(sorted(self.filters.items()))

    sort_by = OrderingFilter(
        label='Sort by',
        fields=(('price', 'price'),
                ('name', 'name'))
    )

    class Meta:
        model = Product
        fields = ['price']
        filter_overrides = {
            PriceField: {
                'filter_class': RangeFilter
            }
        }

    @property
    def product_attributes_filter_form(self):
        """
        This method returns only those filters that ware dynamically generated
        in __init__().
        In this case 'price' and 'sort_by' are rendered in template differently
        than rest of the filters.
        :return:
        """
        form = deepcopy(self.form)
        del form.fields['price']
        del form.fields['sort_by']
        return form


def get_attribute_choices(attribute):
    return [(choice.pk, choice.name) for choice in attribute.values.all()]

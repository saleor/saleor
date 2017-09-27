from collections import OrderedDict

from django_filters import FilterSet, MultipleChoiceFilter, RangeFilter, \
    OrderingFilter
from django.forms import CheckboxSelectMultiple

from django_prices.models import PriceField

from .models import Product, AttributeChoiceValue


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
            self.filters[attribute.slug] = \
                MultipleChoiceFilter(
                    name='attributes__%s' % attribute.pk,
                    label=attribute.name,
                    widget=CheckboxSelectMultiple,
                    choices=get_attribute_choices(attribute))

        for attribute in variant_attributes:
            self.filters[attribute.slug] = \
                MultipleChoiceFilter(
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
        exclude = []
        filter_overrides = {
            PriceField: {
                'filter_class': RangeFilter
            }
        }


def get_attribute_choices(attribute):
    result = [(choice.pk, choice.name)
              for choice in
              AttributeChoiceValue.objects.filter(attribute__pk=attribute.pk)]
    return result

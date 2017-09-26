from django_filters import FilterSet, MultipleChoiceFilter, RangeFilter
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
                    name='product_class__product_attributes__values__slug',
                    label=attribute.name,
                    widget=CheckboxSelectMultiple,
                    choices=get_attribute_choices(attribute))

        for attribute in variant_attributes:
            self.filters[attribute.slug] = \
                MultipleChoiceFilter(
                    name='product_class__variant_attributes__values__slug',
                    label=attribute.name,
                    widget=CheckboxSelectMultiple,
                    choices=get_attribute_choices(attribute))

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
    result = [(choice.slug, choice.name)
              for choice in AttributeChoiceValue.objects.filter(
            attribute__slug=attribute.slug)]
    return result

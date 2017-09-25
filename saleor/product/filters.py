from django_filters import FilterSet, MultipleChoiceFilter, RangeFilter
from django.forms import CheckboxSelectMultiple

from django_prices.models import PriceField

from .models import Product, AttributeChoiceValue


class ProductFilter(FilterSet):
    def __init__(self, *args, **kwargs):
        super(ProductFilter, self).__init__(*args, **kwargs)
        self.products = self.queryset

        product_attributes = set()
        variant_attributes = set()
        for product in self.products:
            for attribute in product.product_class.variant_attributes.all():
                product_attributes.add(attribute)
            for attribute in product.product_class.product_attributes.all():
                variant_attributes.add(attribute)

        for attribute in product_attributes:
            self.filters[attribute.slug] = \
                MultipleChoiceFilter(
                    name='product_class__product_attributes__values__slug',
                    label=attribute.name,
                    widget=CheckboxSelectMultiple,
                    choices=self.get_attribute_choices(attribute)
                )

        for attribute in variant_attributes:
            self.filters[attribute.slug] = \
                MultipleChoiceFilter(
                    name='product_class__variant_attributes__values__slug',
                    label=attribute.name,
                    widget=CheckboxSelectMultiple,
                    choices=self.get_attribute_choices(attribute)
                )

    def get_attribute_choices(self, attribute):
        result = [(choice.slug, choice.name)
                  for choice in AttributeChoiceValue.objects
                      .filter(attribute__name=attribute.name)]
        return result

    class Meta:
        model = Product
        fields = ['price']
        exclude = []
        filter_overrides = {
            PriceField: {
                'filter_class': RangeFilter
            }
        }

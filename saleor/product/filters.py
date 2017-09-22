from django_filters import FilterSet, ModelMultipleChoiceFilter

from django.forms import CheckboxSelectMultiple

from .models import Category, Product, ProductAttribute, AttributeChoiceValue


class CategoryFilter(FilterSet):
    class Meta:
        model = Category
        fields = ['name', 'parent']


class ProductFilter(FilterSet):
    class Meta:
        model = Product
        fields = ['price', 'categories__name']


class ProductAttributeFilter(FilterSet):
    def __init__(self, *args, **kwargs):
        self.attribute_name = kwargs.pop('attribute_name')
        super(ProductAttributeFilter, self).__init__(*args, **kwargs)
        self.filters['name'].queryset = \
            AttributeChoiceValue.objects.all().filter(
                attribute__name=self.attribute_name)

    name = ModelMultipleChoiceFilter(widget=CheckboxSelectMultiple)

    class Meta:
        model = ProductAttribute
        fields = ['name']



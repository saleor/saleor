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
        self.product_attributes, self.variant_attributes = (
            self._get_attributes())
        self.filters.update(self._get_product_attributes_filters())
        self.filters.update(self._get_product_variants_attributes_filters())
        self.filters = OrderedDict(sorted(self.filters.items()))

    def _get_attributes(self):
        q_product_attributes = self._get_product_attributes_lookup()
        q_variant_attributes = self._get_variant_attributes_lookup()
        product_attributes = (
            Attribute.objects.all()
            .prefetch_related('translations', 'values__translations')
            .filter(q_product_attributes)
            .distinct())
        variant_attributes = (
            Attribute.objects.all()
            .prefetch_related('translations', 'values__translations')
            .filter(q_variant_attributes)
            .distinct())
        return product_attributes, variant_attributes

    def _get_product_attributes_lookup(self):
        raise NotImplementedError()

    def _get_variant_attributes_lookup(self):
        raise NotImplementedError()

    def _get_product_attributes_filters(self):
        filters = {}
        for attribute in self.product_attributes:
            filters[attribute.slug] = MultipleChoiceFilter(
                field_name='attributes__%s' % attribute.pk,
                label=attribute.translated.name,
                widget=CheckboxSelectMultiple,
                choices=self._get_attribute_choices(attribute))
        return filters

    def _get_product_variants_attributes_filters(self):
        filters = {}
        for attribute in self.variant_attributes:
            filters[attribute.slug] = MultipleChoiceFilter(
                field_name='variants__attributes__%s' % attribute.pk,
                label=attribute.translated.name,
                widget=CheckboxSelectMultiple,
                choices=self._get_attribute_choices(attribute))
        return filters

    def _get_attribute_choices(self, attribute):
        return [
            (choice.pk, choice.translated.name)
            for choice in attribute.values.all()]


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

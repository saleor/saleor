from collections import OrderedDict
from itertools import chain

from django.db.models import Q
from django.forms import CheckboxSelectMultiple
from django.utils.translation import pgettext_lazy
from django_filters import MultipleChoiceFilter, OrderingFilter, RangeFilter

from ..core.filters import SortedFilterSet
from .models import Attribute, Product

SORT_BY_FIELDS = OrderedDict(
    [
        ("name", pgettext_lazy("Product list sorting option", "name")),
        (
            "minimal_variant_price_amount",
            pgettext_lazy("Product list sorting option", "price"),
        ),
        ("updated_at", pgettext_lazy("Product list sorting option", "last updated")),
    ]
)


class JSONBArrayFilter(MultipleChoiceFilter):
    def get_filter_predicate(self, v):
        operator = f"{self.field_name}__has_key"
        try:
            return {operator: getattr(v, self.field.to_field_name)}
        except (AttributeError, TypeError):
            return {operator: v}


class ProductFilter(SortedFilterSet):
    sort_by = OrderingFilter(
        label=pgettext_lazy("Product list sorting form", "Sort by"),
        fields=SORT_BY_FIELDS.keys(),
        field_labels=SORT_BY_FIELDS,
    )
    minimal_variant_price = RangeFilter(
        label=pgettext_lazy("Currency amount", "Price"),
        field_name="minimal_variant_price_amount",
    )

    class Meta:
        model = Product
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        attributes = self._get_attributes()
        filters = {}
        for attribute in attributes:
            filters[attribute.slug] = JSONBArrayFilter(
                field_name=f"attributes__from_key_{attribute.pk}",
                label=attribute.translated.name,
                widget=CheckboxSelectMultiple,
                choices=self._get_attribute_choices(attribute),
            )
        self.filters.update(filters)

    def _get_attributes(self):
        q_product_attributes = self._get_product_attributes_lookup()
        q_variant_attributes = self._get_variant_attributes_lookup()
        product_attributes = (
            Attribute.objects.prefetch_related("translations", "values__translations")
            .exclude(filterable_in_storefront=False)
            .filter(q_product_attributes)
            .distinct()
        )
        variant_attributes = (
            Attribute.objects.prefetch_related("translations", "values__translations")
            .exclude(filterable_in_storefront=False)
            .filter(q_variant_attributes)
            .distinct()
        )

        attributes = chain(product_attributes, variant_attributes)
        attributes = sorted(
            attributes, key=lambda attr: attr.storefront_search_position
        )
        return attributes

    def _get_product_attributes_lookup(self):
        raise NotImplementedError()

    def _get_variant_attributes_lookup(self):
        raise NotImplementedError()

    def _get_attribute_choices(self, attribute):
        return [
            (choice.pk, choice.translated.name) for choice in attribute.values.all()
        ]


class ProductCategoryFilter(ProductFilter):
    def __init__(self, *args, **kwargs):
        self.category = kwargs.pop("category")
        super().__init__(*args, **kwargs)

    def _get_product_attributes_lookup(self):
        categories = self.category.get_descendants(include_self=True)
        return Q(product_types__products__category__in=categories)

    def _get_variant_attributes_lookup(self):
        categories = self.category.get_descendants(include_self=True)
        return Q(product_variant_types__products__category__in=categories)


class ProductCollectionFilter(ProductFilter):
    def __init__(self, *args, **kwargs):
        self.collection = kwargs.pop("collection")
        super().__init__(*args, **kwargs)

    def _get_product_attributes_lookup(self):
        return Q(product_types__products__collections=self.collection)

    def _get_variant_attributes_lookup(self):
        return Q(product_variant_types__products__collections=self.collection)

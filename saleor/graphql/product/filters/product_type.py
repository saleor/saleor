import django_filters
import graphene
from django.db.models import Q

from ....product.models import ProductType
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.filters import (
    EnumFilter,
    FilterInputObjectType,
    GlobalIDMultipleChoiceFilter,
    ListObjectTypeFilter,
    MetadataFilterBase,
)
from ...utils.filters import filter_slug_list
from ..enums import (
    ProductTypeConfigurable,
    ProductTypeEnum,
    ProductTypeKindEnum,
)


def filter_product_type_configurable(qs, _, value):
    if value == ProductTypeConfigurable.CONFIGURABLE:
        qs = qs.filter(has_variants=True)
    elif value == ProductTypeConfigurable.SIMPLE:
        qs = qs.filter(has_variants=False)
    return qs


def filter_product_type(qs, _, value):
    if value == ProductTypeEnum.DIGITAL:
        qs = qs.filter(is_digital=True)
    elif value == ProductTypeEnum.SHIPPABLE:
        qs = qs.filter(is_shipping_required=True)
    return qs


def filter_product_type_kind(qs, _, value):
    if value:
        qs = qs.filter(kind=value)
    return qs


class ProductTypeFilter(MetadataFilterBase):
    search = django_filters.CharFilter(method="filter_product_type_searchable")

    configurable = EnumFilter(
        input_class=ProductTypeConfigurable, method=filter_product_type_configurable
    )

    product_type = EnumFilter(input_class=ProductTypeEnum, method=filter_product_type)
    kind = EnumFilter(input_class=ProductTypeKindEnum, method=filter_product_type_kind)
    ids = GlobalIDMultipleChoiceFilter(field_name="id")
    slugs = ListObjectTypeFilter(input_class=graphene.String, method=filter_slug_list)

    class Meta:
        model = ProductType
        fields = ["search", "configurable", "product_type"]

    @classmethod
    def filter_product_type_searchable(cls, queryset, _name, value):
        if not value:
            return queryset
        name_slug_qs = Q(name__ilike=value) | Q(slug__ilike=value)
        return queryset.filter(name_slug_qs)


class ProductTypeFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        filterset_class = ProductTypeFilter

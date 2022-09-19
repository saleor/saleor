import django_filters
import graphene
from django.db.models import Q

from ...attribute.models import Attribute, AttributeValue
from ...core.permissions import has_one_of_permissions
from ...product import models
from ...product.models import ALL_PRODUCTS_PERMISSIONS
from ..attribute.enums import AttributeTypeEnum
from ..channel.filters import get_channel_slug_from_filter_data
from ..core.filters import (
    EnumFilter,
    GlobalIDFilter,
    GlobalIDMultipleChoiceFilter,
    ListObjectTypeFilter,
    MetadataFilterBase,
    filter_slug_list,
)
from ..core.types import ChannelFilterInputObjectType, FilterInputObjectType
from ..core.utils import from_global_id_or_error
from ..utils import get_user_or_app_from_context


def filter_attributes_by_product_types(qs, field, value, requestor, channel_slug):
    if not value:
        return qs

    product_qs = models.Product.objects.visible_to_user(requestor, channel_slug)

    if field == "in_category":
        _type, category_id = from_global_id_or_error(value, "Category")
        category = models.Category.objects.filter(pk=category_id).first()

        if category is None:
            return qs.none()

        tree = category.get_descendants(include_self=True)
        product_qs = product_qs.filter(category__in=tree)

        if not has_one_of_permissions(requestor, ALL_PRODUCTS_PERMISSIONS):
            product_qs = product_qs.annotate_visible_in_listings(channel_slug).exclude(
                visible_in_listings=False
            )

    elif field == "in_collection":
        _type, collection_id = from_global_id_or_error(value, "Collection")
        product_qs = product_qs.filter(collections__id=collection_id)

    else:
        raise NotImplementedError(f"Filtering by {field} is unsupported")

    product_types = set(product_qs.values_list("product_type_id", flat=True))
    return qs.filter(
        Q(product_types__in=product_types) | Q(product_variant_types__in=product_types)
    )


def filter_attribute_type(qs, _, value):
    if not value:
        return qs
    return qs.filter(type=value)


class AttributeValueFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search")
    ids = GlobalIDMultipleChoiceFilter(field_name="id")

    class Meta:
        model = AttributeValue
        fields = ["search"]

    @classmethod
    def filter_search(cls, queryset, _name, value):
        if not value:
            return queryset
        name_slug_qs = Q(name__ilike=value) | Q(slug__ilike=value)

        return queryset.filter(name_slug_qs)


class AttributeFilter(MetadataFilterBase):
    search = django_filters.CharFilter(method="filter_attribute_search")
    ids = GlobalIDMultipleChoiceFilter(field_name="id")
    type = EnumFilter(input_class=AttributeTypeEnum, method=filter_attribute_type)

    in_collection = GlobalIDFilter(method="filter_in_collection")
    in_category = GlobalIDFilter(method="filter_in_category")
    slugs = ListObjectTypeFilter(input_class=graphene.String, method=filter_slug_list)

    class Meta:
        model = Attribute
        fields = [
            "value_required",
            "is_variant_only",
            "visible_in_storefront",
            "filterable_in_storefront",
            "filterable_in_dashboard",
            "available_in_grid",
        ]

    def filter_attribute_search(self, qs, _, value):
        return qs.filter(Q(slug__ilike=value) | Q(name__ilike=value))

    def filter_in_collection(self, qs, name, value):
        requestor = get_user_or_app_from_context(self.request)
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return filter_attributes_by_product_types(
            qs, name, value, requestor, channel_slug
        )

    def filter_in_category(self, qs, name, value):
        requestor = get_user_or_app_from_context(self.request)
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return filter_attributes_by_product_types(
            qs, name, value, requestor, channel_slug
        )


class AttributeFilterInput(ChannelFilterInputObjectType):
    class Meta:
        filterset_class = AttributeFilter


class AttributeValueFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = AttributeValueFilter

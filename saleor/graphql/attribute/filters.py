import django_filters
from django.db.models import Q
from graphene_django.filter import GlobalIDFilter, GlobalIDMultipleChoiceFilter

from ...account.utils import requestor_is_staff_member_or_app
from ...attribute.models import Attribute, AttributeValue
from ...product import models
from ..attribute.enums import AttributeTypeEnum
from ..channel.filters import get_channel_slug_from_filter_data
from ..core.filters import EnumFilter, MetadataFilterBase
from ..core.types import FilterInputObjectType
from ..core.utils import from_global_id_or_error
from ..utils import get_user_or_app_from_context
from ..utils.filters import filter_fields_containing_value


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

        if not requestor_is_staff_member_or_app(requestor):
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

    class Meta:
        model = AttributeValue
        fields = ["search"]

    @classmethod
    def filter_search(cls, queryset, _name, value):
        if not value:
            return queryset
        name_slug_qs = Q(name__trigram_similar=value) | Q(slug__trigram_similar=value)

        return queryset.filter(name_slug_qs)


class AttributeFilter(MetadataFilterBase):
    # Search by attribute name and slug
    search = django_filters.CharFilter(
        method=filter_fields_containing_value("slug", "name")
    )
    ids = GlobalIDMultipleChoiceFilter(field_name="id")
    type = EnumFilter(input_class=AttributeTypeEnum, method=filter_attribute_type)

    in_collection = GlobalIDFilter(method="filter_in_collection")
    in_category = GlobalIDFilter(method="filter_in_category")

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

    def filter_in_collection(self, queryset, name, value):
        requestor = get_user_or_app_from_context(self.request)
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return filter_attributes_by_product_types(
            queryset, name, value, requestor, channel_slug
        )

    def filter_in_category(self, queryset, name, value):
        requestor = get_user_or_app_from_context(self.request)
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return filter_attributes_by_product_types(
            queryset, name, value, requestor, channel_slug
        )


class AttributeFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = AttributeFilter


class AttributeValueFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = AttributeValueFilter

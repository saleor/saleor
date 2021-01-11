import django_filters
from django.db.models import Q
from graphene_django.filter import GlobalIDFilter, GlobalIDMultipleChoiceFilter

from ...account.utils import requestor_is_staff_member_or_app
from ...attribute.models import Attribute
from ...product.models import Category, Product
from ..attribute.enums import AttributeTypeEnum
from ..channel.filters import get_channel_slug_from_filter_data
from ..core.filters import EnumFilter
from ..core.types import ChannelFilterInputObjectType
from ..core.utils import from_global_id_strict_type
from ..utils import get_user_or_app_from_context
from ..utils.filters import filter_fields_containing_value


def filter_attributes_by_product_types(qs, field, value, requestor, channel_slug):
    if not value:
        return qs

    product_qs = Product.objects.visible_to_user(requestor, channel_slug)

    if field == "in_category":
        category_id = from_global_id_strict_type(
            value, only_type="Category", field=field
        )
        category = Category.objects.filter(pk=category_id).first()

        if category is None:
            return qs.none()

        tree = category.get_descendants(include_self=True)
        product_qs = product_qs.filter(category__in=tree)

        if not requestor_is_staff_member_or_app(requestor):
            product_qs = product_qs.annotate_visible_in_listings(channel_slug).exclude(
                visible_in_listings=False
            )

    elif field == "in_collection":
        collection_id = from_global_id_strict_type(
            value, only_type="Collection", field=field
        )
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


class AttributeFilter(django_filters.FilterSet):
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


class AttributeFilterInput(ChannelFilterInputObjectType):
    class Meta:
        filterset_class = AttributeFilter

import django_filters
import graphene
from django.db.models import Q

from ....product.models import (
    Collection,
)
from ...channel.filters import get_channel_slug_from_filter_data
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.filters import (
    ChannelFilterInputObjectType,
    EnumFilter,
    GlobalIDMultipleChoiceFilter,
    GlobalIDMultipleChoiceWhereFilter,
    ListObjectTypeFilter,
    MetadataFilterBase,
    MetadataWhereFilterBase,
)
from ...core.filters.where_input import (
    WhereInputObjectType,
)
from ...utils.filters import (
    filter_by_ids,
    filter_slug_list,
)
from ..enums import (
    CollectionPublished,
)


def _filter_collections_is_published(qs, _, value, channel_slug):
    return qs.filter(
        channel_listings__is_published=value,
        channel_listings__channel__slug=channel_slug,
    )


class CollectionFilter(MetadataFilterBase):
    published = EnumFilter(
        input_class=CollectionPublished, method="filter_is_published"
    )
    search = django_filters.CharFilter(method="collection_filter_search")
    ids = GlobalIDMultipleChoiceFilter(field_name="id")
    slugs = ListObjectTypeFilter(input_class=graphene.String, method=filter_slug_list)

    class Meta:
        model = Collection
        fields = ["published", "search"]

    def collection_filter_search(self, queryset, _name, value):
        if not value:
            return queryset
        name_slug_qs = Q(name__ilike=value) | Q(slug__ilike=value)
        return queryset.filter(name_slug_qs)

    def filter_is_published(self, queryset, name, value):
        channel_slug = get_channel_slug_from_filter_data(self.data)
        if value == CollectionPublished.PUBLISHED:
            return _filter_collections_is_published(queryset, name, True, channel_slug)
        if value == CollectionPublished.HIDDEN:
            return _filter_collections_is_published(queryset, name, False, channel_slug)
        return queryset


class CollectionWhere(MetadataWhereFilterBase):
    ids = GlobalIDMultipleChoiceWhereFilter(method=filter_by_ids("Collection"))
    # Collection where filter is also used in promotion logic. In case of extending it
    # the collection update mutation should also be modified to recalculate the prices
    # for new added field.

    class Meta:
        model = Collection
        fields = []


class CollectionFilterInput(ChannelFilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        filterset_class = CollectionFilter


class CollectionWhereInput(WhereInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        filterset_class = CollectionWhere

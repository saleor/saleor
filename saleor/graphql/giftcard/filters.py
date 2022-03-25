from typing import List
from uuid import UUID

import django_filters
import graphene
from django.db.models import Exists, OuterRef, Q
from graphql.error import GraphQLError

from ...account import models as account_models
from ...giftcard import models
from ...order import models as order_models
from ...product import models as product_models
from ..core.filters import (
    GlobalIDMultipleChoiceFilter,
    ListObjectTypeFilter,
    MetadataFilterBase,
    ObjectTypeFilter,
)
from ..core.types import FilterInputObjectType, NonNullList, PriceRangeInput
from ..utils import resolve_global_ids_to_primary_keys
from .enums import GiftCardEventsEnum


def filter_products(qs, _, value):
    if value:
        _, product_pks = resolve_global_ids_to_primary_keys(value, "Product")
        qs = filter_gift_cards_by_products(qs, product_pks)
    return qs


def filter_gift_cards_by_products(qs, product_ids):
    products = product_models.Product.objects.filter(pk__in=product_ids)
    return qs.filter(Exists(products.filter(pk=OuterRef("product_id"))))


def filter_used_by(qs, _, value):
    if value:
        _, user_pks = resolve_global_ids_to_primary_keys(value, "User")
        qs = filter_gift_cards_by_used_by_user(qs, user_pks)
    return qs


def filter_gift_cards_by_used_by_user(qs, user_pks):
    users = account_models.User.objects.filter(pk__in=user_pks)
    return qs.filter(Exists(users.filter(pk=OuterRef("used_by_id"))))


def filter_tags_list(qs, _, value):
    if not value:
        return qs
    tags = models.GiftCardTag.objects.filter(name__in=value)
    return qs.filter(Exists(tags.filter(pk=OuterRef("tags__id"))))


def filter_gift_card_used(qs, _, value):
    if value is None:
        return qs
    return qs.filter(used_by_email__isnull=not value)


def filter_currency(qs, _, value):
    if not value:
        return qs
    return qs.filter(currency=value)


def _filter_by_price(qs, field, value):
    lookup = {}
    if lte := value.get("lte"):
        lookup[f"{field}_amount__lte"] = lte
    if gte := value.get("gte"):
        lookup[f"{field}_amount__gte"] = gte
    return qs.filter(**lookup)


def filter_code(qs, _, value):
    if not value:
        return qs
    return qs.filter(code=value)


class GiftCardFilter(MetadataFilterBase):
    tags = ListObjectTypeFilter(input_class=graphene.String, method=filter_tags_list)
    products = GlobalIDMultipleChoiceFilter(method=filter_products)
    used_by = GlobalIDMultipleChoiceFilter(method=filter_used_by)
    used = django_filters.BooleanFilter(method=filter_gift_card_used)
    currency = django_filters.CharFilter(method=filter_currency)
    current_balance = ObjectTypeFilter(
        input_class=PriceRangeInput, method="filter_current_balance"
    )
    initial_balance = ObjectTypeFilter(
        input_class=PriceRangeInput, method="filter_initial_balance"
    )
    is_active = django_filters.BooleanFilter()
    code = django_filters.CharFilter(method=filter_code)

    class Meta:
        model = models.GiftCard
        fields = ["is_active"]

    def filter_current_balance(self, queryset, name, value):
        check_currency_in_filter_data(self.data)
        return _filter_by_price(queryset, "current_balance", value)

    def filter_initial_balance(self, queryset, name, value):
        check_currency_in_filter_data(self.data)
        return _filter_by_price(queryset, "initial_balance", value)


def check_currency_in_filter_data(filter_data: dict):
    currency = filter_data.get("currency")
    if not currency:
        raise GraphQLError(
            "You must provide a `currency` filter parameter for filtering by price."
        )


class GiftCardFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = GiftCardFilter


def filter_events_by_type(events: List[models.GiftCardEvent], type_value: str):
    filtered_events = []
    for event in events:
        if event.type == type_value:
            filtered_events.append(event)
    return filtered_events


def filter_events_by_orders(events: List[models.GiftCardEvent], order_ids: List[str]):
    order_pks = _get_order_pks(order_ids)

    filtered_events = []
    for event in events:
        if event.order_id in order_pks:
            filtered_events.append(event)
    return filtered_events


def _get_order_pks(order_ids: List[str]):
    _, order_pks = resolve_global_ids_to_primary_keys(order_ids, "Order")

    pks = []
    old_pks = []
    for pk in order_pks:
        try:
            pks.append(UUID(pk))
        except ValueError:
            old_pks.append(pk)

    return order_models.Order.objects.filter(
        Q(id__in=pks) | (Q(use_old_id=True) & Q(number__in=old_pks))
    ).values_list("id", flat=True)


class GiftCardEventFilterInput(graphene.InputObjectType):
    type = graphene.Argument(GiftCardEventsEnum)
    orders = NonNullList(graphene.ID)


def filter_gift_card_tag_search(qs, _, value):
    if not value:
        return qs
    return qs.filter(name__ilike=value)


class GiftCardTagFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_gift_card_tag_search)


class GiftCardTagFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = GiftCardTagFilter

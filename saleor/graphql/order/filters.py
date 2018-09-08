from django.db.models import Q
from django_filters import CharFilter, NumberFilter
from graphene_django.filter.filterset import GlobalIDMultipleChoiceFilter

from ...order import models
from ..core.filters import DistinctFilterSet


class OrderFilter(DistinctFilterSet):
    """Filter class for order query.

    Field id is a GraphQL type ID, while order_id represents database
    primary key.
    """

    id = GlobalIDMultipleChoiceFilter(name='id', label='GraphQL ID')
    order_id = NumberFilter(method='order_id_lookup', label='Database ID')
    created__gte = CharFilter(
        name='created', lookup_expr='gte', label='ISO 8601 standard')
    created__lte = CharFilter(
        name='created', lookup_expr='lte', label='ISO 8601 standard')
    user = CharFilter(method='filter_by_order_customer')

    class Meta:
        model = models.Order
        fields = {
            'status': ['exact'],
            'total_net': ['exact', 'lte', 'gte']}

    def order_id_lookup(self, queryset, name, value):
        return queryset.filter(pk__exact=value)

    def filter_by_order_customer(self, queryset, name, value):
        return queryset.filter(
            Q(user__email__icontains=value) |
            Q(user__default_billing_address__first_name__icontains=value) |
            Q(user__default_billing_address__last_name__icontains=value) |
            Q(user_email__icontains=value))

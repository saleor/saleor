from ...discount import models
from ..utils import filter_by_query_param

VOUCHER_SEARCH_FIELDS = (
    'name', 'code', 'discount_value', 'collections__name', 'products__name',
    'limit', 'countries', 'discount_value_type')

SALE_SEARCH_FIELDS = ('name', 'value', 'type')


def resolve_vouchers(info, query):
    queryset = models.Voucher.objects.all()
    queryset = filter_by_query_param(queryset, query, VOUCHER_SEARCH_FIELDS)
    return queryset


def resolve_sales(info, query):
    queryset = models.Sale.objects.all()
    queryset = filter_by_query_param(queryset, query, SALE_SEARCH_FIELDS)
    return queryset

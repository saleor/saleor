from ...discount import models
from ..utils import filter_by_query_param

VOUCHER_SEARCH_FIELDS = (
    'name', 'code', 'discount_value', 'product__name', 'category__name',
    'limit', 'apply_to', 'discount_value_type')

def resolve_vouchers(info, query):
    queryset = models.Voucher.objects.all()
    queryset = filter_by_query_param(queryset, query, VOUCHER_SEARCH_FIELDS)
    return queryset

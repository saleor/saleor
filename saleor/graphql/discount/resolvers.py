from ...discount import models
from ..utils.filters import filter_by_query_param

VOUCHER_SEARCH_FIELDS = ("name", "code")
SALE_SEARCH_FIELDS = ("name", "value", "type")


def resolve_vouchers(info, query, **_kwargs):
    qs = models.Voucher.objects.all()
    return filter_by_query_param(qs, query, VOUCHER_SEARCH_FIELDS)


def resolve_sales(info, query, **_kwargs):
    qs = models.Sale.objects.all()
    return filter_by_query_param(qs, query, SALE_SEARCH_FIELDS)

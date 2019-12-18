import graphene_django_optimizer as gql_optimizer

from ...discount import models
from ..utils import filter_by_query_param, sort_queryset
from .sorters import SaleSortField, VoucherSortField

VOUCHER_SEARCH_FIELDS = ("name", "code")
SALE_SEARCH_FIELDS = ("name", "value", "type")


def resolve_vouchers(info, query, sort_by=None, **_kwargs):
    qs = models.Voucher.objects.all()
    qs = filter_by_query_param(qs, query, VOUCHER_SEARCH_FIELDS)
    qs = sort_queryset(qs, sort_by, VoucherSortField)
    return gql_optimizer.query(qs, info)


def resolve_sales(info, query, sort_by=None, **_kwargs):
    qs = models.Sale.objects.all()
    qs = filter_by_query_param(qs, query, SALE_SEARCH_FIELDS)
    qs = sort_queryset(qs, sort_by, SaleSortField)
    return gql_optimizer.query(qs, info)

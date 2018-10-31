import graphene_django_optimizer as gql_optimizer

from ...discount import models
from ..utils import filter_by_query_param

VOUCHER_SEARCH_FIELDS = (
    'name', 'code', 'discount_value', 'categories__name', 'collections__name',
    'products__name', 'min_amount_spent', 'countries', 'discount_value_type',
    'apply_one_per_order')

SALE_SEARCH_FIELDS = ('name', 'value', 'type')


def resolve_vouchers(info, query):
    qs = models.Voucher.objects.all()
    qs = filter_by_query_param(qs, query, VOUCHER_SEARCH_FIELDS)
    return gql_optimizer.query(qs, info)


def resolve_sales(info, query):
    qs = models.Sale.objects.all()
    qs = filter_by_query_param(qs, query, SALE_SEARCH_FIELDS)
    return gql_optimizer.query(qs, info)

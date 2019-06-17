# flake8: noqa
import graphene_django_optimizer as gql_optimizer

from .common import (
    CountryDisplay,
    Error,
    Image,
    LanguageDisplay,
    PermissionDisplay,
    SeoInput,
    TaxType,
    Weight,
)
from .filter_input import FilterInputObjectType
from .money import VAT, Money, MoneyRange, ReducedRate, TaxedMoney, TaxedMoneyRange
from .upload import Upload


def get_node_optimized(qs, lookup, info):
    qs = qs.filter(**lookup)
    qs = gql_optimizer.query(qs, info)
    return qs[0] if qs else None

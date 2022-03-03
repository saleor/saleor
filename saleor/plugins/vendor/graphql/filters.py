import django_filters

from ....graphql.account.enums import CountryCodeEnum
from ....graphql.core.filters import EnumFilter
from ....graphql.core.types.filter_input import FilterInputObjectType
from .. import models


def filter_vendor_country(qs, _, value):
    return qs.filter(country=value)


class VendorFilter(django_filters.FilterSet):
    country = EnumFilter(input_class=CountryCodeEnum, method=filter_vendor_country)

    class Meta:
        model = models.Vendor
        fields = ["country"]


class VendorFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = VendorFilter

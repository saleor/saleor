import django_filters
from transferrequest.models import TransferRequest
from saleor.graphql.core.types import FilterInputObjectType


class TransferRequestFilter(django_filters.FilterSet):
    approved = django_filters.BooleanFilter(field_name="approved")

    class Meta:
        models = TransferRequest


class TransferRequestInput(FilterInputObjectType):
    class Meta:
        filterset_class = TransferRequestFilter

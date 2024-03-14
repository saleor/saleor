from django.db.models import Exists, OuterRef

from ...tax import models
from ..account.enums import CountryCodeEnum
from ..core.doc_category import DOC_CATEGORY_TAXES
from ..core.filters import (
    GlobalIDMultipleChoiceFilter,
    ListObjectTypeFilter,
    MetadataFilterBase,
)
from ..core.types import FilterInputObjectType
from ..utils.filters import filter_by_id
from .types import TaxClass, TaxConfiguration


def filter_tax_classes_by_country(qs, _, values):
    if values:
        rates = models.TaxClassCountryRate.objects.using(qs.db).filter(
            country__in=values
        )
        qs = qs.filter(Exists(rates.filter(tax_class_id=OuterRef("id"))))
    return qs


class TaxConfigurationFilter(MetadataFilterBase):
    ids = GlobalIDMultipleChoiceFilter(method=filter_by_id(TaxConfiguration))

    class Meta:
        model = models.TaxConfiguration
        fields = []


class TaxConfigurationFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_TAXES
        filterset_class = TaxConfigurationFilter


class TaxClassFilter(MetadataFilterBase):
    ids = GlobalIDMultipleChoiceFilter(method=filter_by_id(TaxClass))
    countries = ListObjectTypeFilter(
        input_class=CountryCodeEnum, method=filter_tax_classes_by_country
    )

    class Meta:
        model = models.TaxClass
        fields = []


class TaxClassFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_TAXES
        filterset_class = TaxClassFilter

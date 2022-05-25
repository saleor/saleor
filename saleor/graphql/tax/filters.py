from ...tax import models
from ..core.filters import GlobalIDMultipleChoiceFilter, MetadataFilterBase
from ..core.types import FilterInputObjectType
from ..utils.filters import filter_by_id
from .types import TaxConfiguration


class TaxConfigurationFilter(MetadataFilterBase):
    ids = GlobalIDMultipleChoiceFilter(method=filter_by_id(TaxConfiguration))

    class Meta:
        model = models.TaxConfiguration
        fields = []


class TaxConfigurationFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = TaxConfigurationFilter

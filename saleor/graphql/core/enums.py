import graphene

from ...core.permissions import MODELS_PERMISSIONS
from ...core import weight, TaxRateType as CoreTaxRateType
from .utils import str_to_enum


class ReportingPeriod(graphene.Enum):
    TODAY = 'TODAY'
    THIS_MONTH = 'THIS_MONTH'


TaxRateType = graphene.Enum(
    'TaxRateType',
    [(str_to_enum(rate[0]), rate[0]) for rate in CoreTaxRateType.CHOICES])


PermissionEnum = graphene.Enum(
    'PermissionEnum', [
        (str_to_enum(codename.split('.')[1]), codename)
        for codename in MODELS_PERMISSIONS])


WeightUnitsEnum = graphene.Enum.from_enum(weight.WeightUnitsEnum)

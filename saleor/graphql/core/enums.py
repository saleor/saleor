import graphene

from ...core import TaxRateType as CoreTaxRateType
from ...core.permissions import MODELS_PERMISSIONS
from ...core.weight import WeightUnits
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


WeightUnitsEnum = graphene.Enum(
    'WeightUnitsEnum',
    [(str_to_enum(unit[0]), unit[0]) for unit in WeightUnits.CHOICES])

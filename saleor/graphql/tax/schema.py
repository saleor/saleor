import graphene

from ...core.permissions.enums import TaxPermissions
from ...tax import models
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.descriptions import ADDED_IN_35, PREVIEW_FEATURE
from ..core.fields import FilterConnectionField, PermissionsField
from ..core.utils import from_global_id_or_error
from .filters import TaxClassFilterInput, TaxConfigurationFilterInput
from .sorters import TaxClassSortingInput
from .types import (
    TaxClass,
    TaxClassCountableConnection,
    TaxConfiguration,
    TaxConfigurationCountableConnection,
)


class TaxQueries(graphene.ObjectType):
    tax_configuration = PermissionsField(
        TaxConfiguration,
        description="Look up a tax configuration." + ADDED_IN_35 + PREVIEW_FEATURE,
        id=graphene.Argument(
            graphene.ID, description="ID of a tax configuration.", required=True
        ),
        permissions=[TaxPermissions.MANAGE_TAXES],
    )
    tax_configurations = FilterConnectionField(
        TaxConfigurationCountableConnection,
        description="List of tax configurations." + ADDED_IN_35 + PREVIEW_FEATURE,
        filter=TaxConfigurationFilterInput(
            description="Filtering options for tax configurations."
        ),
        permissions=[TaxPermissions.MANAGE_TAXES],
    )
    tax_class = PermissionsField(
        TaxClass,
        description="Look up a tax class." + ADDED_IN_35 + PREVIEW_FEATURE,
        id=graphene.Argument(
            graphene.ID, description="ID of a tax class.", required=True
        ),
        permissions=[TaxPermissions.MANAGE_TAXES],
    )
    tax_classes = FilterConnectionField(
        TaxClassCountableConnection,
        description="List of tax classes." + ADDED_IN_35 + PREVIEW_FEATURE,
        sort_by=TaxClassSortingInput(description="Sort tax classes."),
        filter=TaxClassFilterInput(description="Filtering options for tax classes."),
        permissions=[TaxPermissions.MANAGE_TAXES],
    )

    @staticmethod
    def resolve_tax_configuration(_root, _info, id):
        _, id = from_global_id_or_error(id, TaxConfiguration)
        return models.TaxConfiguration.objects.filter(id=id).first()

    @staticmethod
    def resolve_tax_configurations(_root, info, **kwargs):
        qs = models.TaxConfiguration.objects.all()
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(
            qs, info, kwargs, TaxConfigurationCountableConnection
        )

    @staticmethod
    def resolve_tax_class(_root, _info, id):
        _, id = from_global_id_or_error(id, TaxClass)
        return models.TaxClass.objects.filter(id=id).first()

    @staticmethod
    def resolve_tax_classes(_root, info, **kwargs):
        qs = models.TaxClass.objects.all()
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, TaxClassCountableConnection)


class TaxMutations(graphene.ObjectType):
    pass

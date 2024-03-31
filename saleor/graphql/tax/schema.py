from collections import defaultdict

import graphene
from django_countries.fields import Country

from ...permission.auth_filters import AuthorizationFilters
from ...tax import models
from ..account.enums import CountryCodeEnum
from ..core import ResolveInfo
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.context import get_database_connection_name
from ..core.descriptions import ADDED_IN_39
from ..core.doc_category import DOC_CATEGORY_TAXES
from ..core.fields import FilterConnectionField, PermissionsField
from ..core.types import NonNullList
from ..core.utils import from_global_id_or_error
from .filters import TaxClassFilterInput, TaxConfigurationFilterInput
from .mutations import (
    TaxClassCreate,
    TaxClassDelete,
    TaxClassUpdate,
    TaxConfigurationUpdate,
    TaxCountryConfigurationDelete,
    TaxCountryConfigurationUpdate,
    TaxExemptionManage,
)
from .sorters import TaxClassSortingInput
from .types import (
    TaxClass,
    TaxClassCountableConnection,
    TaxConfiguration,
    TaxConfigurationCountableConnection,
    TaxCountryConfiguration,
)


class TaxQueries(graphene.ObjectType):
    tax_configuration = PermissionsField(
        TaxConfiguration,
        description="Look up a tax configuration." + ADDED_IN_39,
        id=graphene.Argument(
            graphene.ID, description="ID of a tax configuration.", required=True
        ),
        permissions=[
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            AuthorizationFilters.AUTHENTICATED_APP,
        ],
        doc_category=DOC_CATEGORY_TAXES,
    )
    tax_configurations = FilterConnectionField(
        TaxConfigurationCountableConnection,
        description="List of tax configurations." + ADDED_IN_39,
        filter=TaxConfigurationFilterInput(
            description="Filtering options for tax configurations."
        ),
        permissions=[
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            AuthorizationFilters.AUTHENTICATED_APP,
        ],
        doc_category=DOC_CATEGORY_TAXES,
    )
    tax_class = PermissionsField(
        TaxClass,
        description="Look up a tax class." + ADDED_IN_39,
        id=graphene.Argument(
            graphene.ID, description="ID of a tax class.", required=True
        ),
        permissions=[
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            AuthorizationFilters.AUTHENTICATED_APP,
        ],
        doc_category=DOC_CATEGORY_TAXES,
    )
    tax_classes = FilterConnectionField(
        TaxClassCountableConnection,
        description="List of tax classes." + ADDED_IN_39,
        sort_by=TaxClassSortingInput(description="Sort tax classes."),
        filter=TaxClassFilterInput(description="Filtering options for tax classes."),
        permissions=[
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            AuthorizationFilters.AUTHENTICATED_APP,
        ],
        doc_category=DOC_CATEGORY_TAXES,
    )
    tax_country_configuration = PermissionsField(
        TaxCountryConfiguration,
        country_code=graphene.Argument(
            CountryCodeEnum,
            description="Country for which to return tax class rates.",
            required=True,
        ),
        description="Tax class rates grouped by country.",
        permissions=[
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            AuthorizationFilters.AUTHENTICATED_APP,
        ],
        doc_category=DOC_CATEGORY_TAXES,
    )
    tax_country_configurations = PermissionsField(
        NonNullList(
            TaxCountryConfiguration,
            description="A list of countries with grouped tax class rates.",
            required=True,
        ),
        permissions=[
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            AuthorizationFilters.AUTHENTICATED_APP,
        ],
        doc_category=DOC_CATEGORY_TAXES,
    )

    @staticmethod
    def resolve_tax_configuration(_root, info: ResolveInfo, id):
        _, id = from_global_id_or_error(id, TaxConfiguration)
        return (
            models.TaxConfiguration.objects.using(
                get_database_connection_name(info.context)
            )
            .filter(id=id)
            .first()
        )

    @staticmethod
    def resolve_tax_configurations(_root, info: ResolveInfo, **kwargs):
        qs = models.TaxConfiguration.objects.using(
            get_database_connection_name(info.context)
        ).all()
        allow_replica = getattr(info.context, "allow_replica", True)
        qs = filter_connection_queryset(qs, kwargs, allow_replica=allow_replica)
        return create_connection_slice(
            qs, info, kwargs, TaxConfigurationCountableConnection
        )

    @staticmethod
    def resolve_tax_class(_root, info: ResolveInfo, id):
        _, id = from_global_id_or_error(id, TaxClass)
        return (
            models.TaxClass.objects.using(get_database_connection_name(info.context))
            .filter(id=id)
            .first()
        )

    @staticmethod
    def resolve_tax_classes(_root, info: ResolveInfo, **kwargs):
        qs = models.TaxClass.objects.using(
            get_database_connection_name(info.context)
        ).all()
        allow_replica = getattr(info.context, "allow_replica", True)
        qs = filter_connection_queryset(qs, kwargs, allow_replica=allow_replica)
        return create_connection_slice(qs, info, kwargs, TaxClassCountableConnection)

    @staticmethod
    def resolve_tax_country_configuration(_root, info: ResolveInfo, country_code):
        country_rates = models.TaxClassCountryRate.objects.using(
            get_database_connection_name(info.context)
        ).filter(country=country_code)
        return TaxCountryConfiguration(
            country=Country(country_code),
            tax_class_country_rates=country_rates,
        )

    @staticmethod
    def resolve_tax_country_configurations(_root, info: ResolveInfo, **kwargs):
        country_rates = models.TaxClassCountryRate.objects.using(
            get_database_connection_name(info.context)
        ).all()
        rates_per_country = defaultdict(list)
        for country_rate in country_rates:
            rates_per_country[country_rate.country].append(country_rate)
        return [
            TaxCountryConfiguration(
                country=country, tax_class_country_rates=rates_per_country[country]
            )
            for country in rates_per_country
        ]


class TaxMutations(graphene.ObjectType):
    tax_class_create = TaxClassCreate.Field()
    tax_class_delete = TaxClassDelete.Field()
    tax_class_update = TaxClassUpdate.Field()
    tax_configuration_update = TaxConfigurationUpdate.Field()
    tax_country_configuration_update = TaxCountryConfigurationUpdate.Field()
    tax_country_configuration_delete = TaxCountryConfigurationDelete.Field()
    tax_exemption_manage = TaxExemptionManage.Field()

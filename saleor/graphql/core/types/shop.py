import graphene
from django.conf import settings
from django_countries import countries
from django_prices_vatlayer import models as vatlayer_models
from graphql_jwt.decorators import permission_required
from phonenumbers import COUNTRY_CODE_TO_REGION_CODE

from ....core.permissions import get_permissions
from ....site import models as site_models
from ...utils import format_permissions_for_display
from .common import CountryDisplay, LanguageDisplay, PermissionDisplay
from .money import VAT


class AuthorizationKey(graphene.ObjectType):
    name = graphene.String(description='Name of the key.', required=True)
    key = graphene.String(description='Value of the key.', required=True)


class Domain(graphene.ObjectType):
    host = graphene.String(
        description='The host name of the domain.', required=True)
    ssl_enabled = graphene.Boolean(
        description='Inform if SSL is enabled.', required=True)
    url = graphene.String(
        description='Shop\'s absolute URL.', required=True)

    class Meta:
        description = 'Represents shop\'s domain.'


class Shop(graphene.ObjectType):
    authorization_keys = graphene.List(
        AuthorizationKey, description='List of configured authorization keys.',
        required=True)
    countries = graphene.List(
        CountryDisplay, description='List of countries available in the shop.',
        required=True)
    currencies = graphene.List(
        graphene.String, description='List of available currencies.',
        required=True)
    default_currency = graphene.String(
        description='Default shop\'s currency.', required=True)
    description = graphene.String(description='Shop\'s description.')
    domain = graphene.Field(
        Domain, required=True, description='Shop\'s domain data.')
    languages = graphene.List(
        LanguageDisplay,
        description='List of the shops\'s supported languages.', required=True)
    name = graphene.String(description='Shop\'s name.', required=True)
    permissions = graphene.List(
        PermissionDisplay, description='List of available permissions.',
        required=True)
    phone_prefixes = graphene.List(
        graphene.String, description='List of possible phone prefixes.',
        required=True)
    tax_rates = graphene.List(
        VAT, description='List of VAT tax rates configured in the shop.',
        required=True)
    tax_rate = graphene.Field(
        VAT, description='VAT tax rates for a specific country.',
        required=True, country_code=graphene.Argument(graphene.String))

    class Meta:
        description = '''
        Represents a shop resource containing general shop\'s data
        and configuration.'''

    @permission_required('site.manage_settings')
    def resolve_authorization_keys(self, info):
        return site_models.AuthorizationKey.objects.all()

    def resolve_countries(self, info):
        return [
            CountryDisplay(code=country[0], country=country[1])
            for country in countries]

    def resolve_currencies(self, info):
        return settings.AVAILABLE_CURRENCIES

    def resolve_domain(self, info):
        site = info.context.site
        return Domain(
            host=site.domain,
            ssl_enabled=settings.ENABLE_SSL,
            url=info.context.build_absolute_uri('/'))

    def resolve_default_currency(self, info):
        return settings.DEFAULT_CURRENCY

    def resolve_description(self, info):
        return info.context.site.settings.description

    def resolve_languages(self, info):
        return [
            LanguageDisplay(code=language[0], language=language[1])
            for language in settings.LANGUAGES]

    def resolve_name(self, info):
        return info.context.site.name

    @permission_required('site.manage_settings')
    def resolve_permissions(self, info):
        permissions = get_permissions()
        return format_permissions_for_display(permissions)

    def resolve_phone_prefixes(self, info):
        return list(COUNTRY_CODE_TO_REGION_CODE.keys())

    @permission_required('site.manage_settings')
    def resolve_tax_rates(self, info):
        return vatlayer_models.VAT.objects.order_by('country_code')

    @permission_required('site.manage_settings')
    def resolve_tax_rate(self, info, country_code):
        # country codes for VAT rates are stored uppercase
        country_code = country_code.upper()
        return vatlayer_models.VAT.objects.filter(
            country_code=country_code).first()

import graphene
from django.conf import settings
from django.utils import translation
from django_countries import countries
from django_prices_vatlayer.models import VAT
from phonenumbers import COUNTRY_CODE_TO_REGION_CODE

from ...account import models as account_models
from ...core.permissions import SitePermissions, get_permissions
from ...core.utils import get_client_ip, get_country_by_ip
from ...menu import models as menu_models
from ...plugins.manager import get_plugins_manager
from ...product import models as product_models
from ...site import models as site_models
from ..account.types import Address, StaffNotificationRecipient
from ..checkout.types import PaymentGateway
from ..core.enums import WeightUnitsEnum
from ..core.types.common import CountryDisplay, LanguageDisplay, Permission
from ..core.utils import str_to_enum
from ..decorators import permission_required
from ..menu.types import Menu
from ..product.types import Collection
from ..translations.enums import LanguageCodeEnum
from ..translations.fields import TranslationField
from ..translations.resolvers import resolve_translation
from ..translations.types import ShopTranslation
from ..utils import format_permissions_for_display
from .enums import AuthorizationKeyType


class Navigation(graphene.ObjectType):
    main = graphene.Field(Menu, description="Main navigation bar.")
    secondary = graphene.Field(Menu, description="Secondary navigation bar.")

    class Meta:
        description = "Represents shop's navigation menus."


class AuthorizationKey(graphene.ObjectType):
    name = AuthorizationKeyType(
        description="Name of the authorization backend.", required=True
    )
    key = graphene.String(description="Authorization key (client ID).", required=True)


class Domain(graphene.ObjectType):
    host = graphene.String(description="The host name of the domain.", required=True)
    ssl_enabled = graphene.Boolean(
        description="Inform if SSL is enabled.", required=True
    )
    url = graphene.String(description="Shop's absolute URL.", required=True)

    class Meta:
        description = "Represents shop's domain."


class Geolocalization(graphene.ObjectType):
    country = graphene.Field(
        CountryDisplay, description="Country of the user acquired by his IP address."
    )

    class Meta:
        description = "Represents customers's geolocalization data."


class Shop(graphene.ObjectType):
    available_payment_gateways = graphene.List(
        graphene.NonNull(PaymentGateway),
        description="List of available payment gateways.",
        required=True,
    )
    geolocalization = graphene.Field(
        Geolocalization, description="Customer's geolocalization data."
    )
    authorization_keys = graphene.List(
        AuthorizationKey,
        description=(
            "List of configured authorization keys. Authorization keys are used to "
            "enable third-party OAuth authorization (currently Facebook or Google)."
        ),
        required=True,
    )
    countries = graphene.List(
        graphene.NonNull(CountryDisplay),
        language_code=graphene.Argument(
            LanguageCodeEnum,
            description="A language code to return the translation for.",
        ),
        description="List of countries available in the shop.",
        required=True,
    )
    currencies = graphene.List(
        graphene.String, description="List of available currencies.", required=True
    )
    default_currency = graphene.String(
        description="Shop's default currency.", required=True
    )
    default_country = graphene.Field(
        CountryDisplay, description="Shop's default country."
    )
    default_mail_sender_name = graphene.String(
        description="Default shop's email sender's name."
    )
    default_mail_sender_address = graphene.String(
        description="Default shop's email sender's address."
    )
    description = graphene.String(description="Shop's description.")
    domain = graphene.Field(Domain, required=True, description="Shop's domain data.")
    homepage_collection = graphene.Field(
        Collection, description="Collection displayed on homepage."
    )
    languages = graphene.List(
        LanguageDisplay,
        description="List of the shops's supported languages.",
        required=True,
    )
    name = graphene.String(description="Shop's name.", required=True)
    navigation = graphene.Field(Navigation, description="Shop's navigation.")
    permissions = graphene.List(
        Permission, description="List of available permissions.", required=True
    )
    phone_prefixes = graphene.List(
        graphene.String, description="List of possible phone prefixes.", required=True
    )
    header_text = graphene.String(description="Header text.")
    include_taxes_in_prices = graphene.Boolean(
        description="Include taxes in prices.", required=True
    )
    display_gross_prices = graphene.Boolean(
        description="Display prices with tax in store.", required=True
    )
    charge_taxes_on_shipping = graphene.Boolean(
        description="Charge taxes on shipping.", required=True
    )
    track_inventory_by_default = graphene.Boolean(
        description="Enable inventory tracking."
    )
    default_weight_unit = WeightUnitsEnum(description="Default weight unit.")
    translation = TranslationField(ShopTranslation, type_name="shop", resolver=None)
    automatic_fulfillment_digital_products = graphene.Boolean(
        description="Enable automatic fulfillment for all digital products."
    )

    default_digital_max_downloads = graphene.Int(
        description="Default number of max downloads per digital content URL."
    )
    default_digital_url_valid_days = graphene.Int(
        description="Default number of days which digital content URL will be valid."
    )
    company_address = graphene.Field(
        Address, description="Company address.", required=False
    )
    customer_set_password_url = graphene.String(
        description="URL of a view where customers can set their password.",
        required=False,
    )
    staff_notification_recipients = graphene.List(
        StaffNotificationRecipient,
        description="List of staff notification recipients.",
        required=False,
    )

    class Meta:
        description = (
            "Represents a shop resource containing general shop data and configuration."
        )

    @staticmethod
    def resolve_available_payment_gateways(_, _info):
        return [gtw for gtw in get_plugins_manager().list_payment_gateways()]

    @staticmethod
    @permission_required(SitePermissions.MANAGE_SETTINGS)
    def resolve_authorization_keys(_, _info):
        return site_models.AuthorizationKey.objects.all()

    @staticmethod
    def resolve_countries(_, _info, language_code=None):
        taxes = {vat.country_code: vat for vat in VAT.objects.all()}
        with translation.override(language_code):
            return [
                CountryDisplay(
                    code=country[0], country=country[1], vat=taxes.get(country[0])
                )
                for country in countries
            ]

    @staticmethod
    def resolve_currencies(_, _info):
        return settings.AVAILABLE_CURRENCIES

    @staticmethod
    def resolve_domain(_, info):
        site = info.context.site
        return Domain(
            host=site.domain,
            ssl_enabled=settings.ENABLE_SSL,
            url=info.context.build_absolute_uri("/"),
        )

    @staticmethod
    def resolve_geolocalization(_, info):
        client_ip = get_client_ip(info.context)
        country = get_country_by_ip(client_ip)
        if country:
            return Geolocalization(
                country=CountryDisplay(code=country.code, country=country.name)
            )
        return Geolocalization(country=None)

    @staticmethod
    def resolve_default_currency(_, _info):
        return settings.DEFAULT_CURRENCY

    @staticmethod
    def resolve_description(_, info):
        return info.context.site.settings.description

    @staticmethod
    def resolve_homepage_collection(_, info):
        collection_pk = info.context.site.settings.homepage_collection_id
        qs = product_models.Collection.objects.all()
        return qs.filter(pk=collection_pk).first()

    @staticmethod
    def resolve_languages(_, _info):
        return [
            LanguageDisplay(
                code=LanguageCodeEnum[str_to_enum(language[0])], language=language[1]
            )
            for language in settings.LANGUAGES
        ]

    @staticmethod
    def resolve_name(_, info):
        return info.context.site.name

    @staticmethod
    def resolve_navigation(_, info):
        site_settings = info.context.site.settings
        qs = menu_models.Menu.objects.all()
        top_menu = qs.filter(pk=site_settings.top_menu_id).first()
        bottom_menu = qs.filter(pk=site_settings.bottom_menu_id).first()
        return Navigation(main=top_menu, secondary=bottom_menu)

    @staticmethod
    def resolve_permissions(_, _info):
        permissions = get_permissions()
        return format_permissions_for_display(permissions)

    @staticmethod
    def resolve_phone_prefixes(_, _info):
        return list(COUNTRY_CODE_TO_REGION_CODE.keys())

    @staticmethod
    def resolve_header_text(_, info):
        return info.context.site.settings.header_text

    @staticmethod
    def resolve_include_taxes_in_prices(_, info):
        return info.context.site.settings.include_taxes_in_prices

    @staticmethod
    def resolve_display_gross_prices(_, info):
        return info.context.site.settings.display_gross_prices

    @staticmethod
    def resolve_charge_taxes_on_shipping(_, info):
        return info.context.site.settings.charge_taxes_on_shipping

    @staticmethod
    def resolve_track_inventory_by_default(_, info):
        return info.context.site.settings.track_inventory_by_default

    @staticmethod
    def resolve_default_weight_unit(_, info):
        return info.context.site.settings.default_weight_unit

    @staticmethod
    def resolve_default_country(_, _info):
        default_country_code = settings.DEFAULT_COUNTRY
        default_country_name = countries.countries.get(default_country_code)
        if default_country_name:
            vat = VAT.objects.filter(country_code=default_country_code).first()
            default_country = CountryDisplay(
                code=default_country_code, country=default_country_name, vat=vat
            )
        else:
            default_country = None
        return default_country

    @staticmethod
    @permission_required(SitePermissions.MANAGE_SETTINGS)
    def resolve_default_mail_sender_name(_, info):
        return info.context.site.settings.default_mail_sender_name

    @staticmethod
    @permission_required(SitePermissions.MANAGE_SETTINGS)
    def resolve_default_mail_sender_address(_, info):
        return info.context.site.settings.default_mail_sender_address

    @staticmethod
    def resolve_company_address(_, info):
        return info.context.site.settings.company_address

    @staticmethod
    def resolve_customer_set_password_url(_, info):
        return info.context.site.settings.customer_set_password_url

    @staticmethod
    def resolve_translation(_, info, language_code):
        return resolve_translation(info.context.site.settings, info, language_code)

    @staticmethod
    @permission_required(SitePermissions.MANAGE_SETTINGS)
    def resolve_automatic_fulfillment_digital_products(_, info):
        site_settings = info.context.site.settings
        return site_settings.automatic_fulfillment_digital_products

    @staticmethod
    @permission_required(SitePermissions.MANAGE_SETTINGS)
    def resolve_default_digital_max_downloads(_, info):
        return info.context.site.settings.default_digital_max_downloads

    @staticmethod
    @permission_required(SitePermissions.MANAGE_SETTINGS)
    def resolve_default_digital_url_valid_days(_, info):
        return info.context.site.settings.default_digital_url_valid_days

    @staticmethod
    @permission_required(SitePermissions.MANAGE_SETTINGS)
    def resolve_staff_notification_recipients(_, info):
        return account_models.StaffNotificationRecipient.objects.all()

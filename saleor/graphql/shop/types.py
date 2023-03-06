from typing import Optional

import graphene
from django.conf import settings
from django_countries import countries
from django_prices_vatlayer.models import VAT
from phonenumbers import COUNTRY_CODE_TO_REGION_CODE

from ... import __version__
from ...account import models as account_models
from ...channel import models as channel_models
from ...core.permissions import AuthorizationFilters, SitePermissions, get_permissions
from ...core.utils import build_absolute_uri
from ...site import models as site_models
from ..account.types import Address, AddressInput, StaffNotificationRecipient
from ..checkout.types import PaymentGateway
from ..core.descriptions import (
    ADDED_IN_31,
    ADDED_IN_35,
    DEPRECATED_IN_3X_FIELD,
    DEPRECATED_IN_3X_INPUT,
    PREVIEW_FEATURE,
)
from ..core.enums import LanguageCodeEnum, WeightUnitsEnum
from ..core.fields import PermissionsField
from ..core.tracing import traced_resolver
from ..core.types import (
    CountryDisplay,
    LanguageDisplay,
    ModelObjectType,
    NonNullList,
    Permission,
    TimePeriod,
)
from ..core.utils import str_to_enum
from ..plugins.dataloaders import plugin_manager_promise_callback
from ..shipping.types import ShippingMethod
from ..site.dataloaders import load_site_callback
from ..translations.fields import TranslationField
from ..translations.resolvers import resolve_translation
from ..translations.types import ShopTranslation
from ..utils import format_permissions_for_display
from .enums import GiftCardSettingsExpiryTypeEnum
from .filters import CountryFilterInput
from .resolvers import resolve_available_shipping_methods, resolve_countries


class Domain(graphene.ObjectType):
    host = graphene.String(description="The host name of the domain.", required=True)
    ssl_enabled = graphene.Boolean(
        description="Inform if SSL is enabled.", required=True
    )
    url = graphene.String(description="Shop's absolute URL.", required=True)

    class Meta:
        description = "Represents shop's domain."


class OrderSettings(ModelObjectType[site_models.SiteSettings]):
    automatically_confirm_all_new_orders = graphene.Boolean(required=True)
    automatically_fulfill_non_shippable_gift_card = graphene.Boolean(required=True)

    class Meta:
        description = "Order related settings from site settings."
        model = site_models.SiteSettings


class GiftCardSettings(ModelObjectType[site_models.SiteSettings]):
    expiry_type = GiftCardSettingsExpiryTypeEnum(
        description="The gift card expiry type settings.", required=True
    )
    expiry_period = graphene.Field(
        TimePeriod, description="The gift card expiry period settings.", required=False
    )

    class Meta:
        description = "Gift card related settings from site settings."
        model = site_models.SiteSettings

    def resolve_expiry_type(root, info):
        return root.gift_card_expiry_type

    def resolve_expiry_period(root, info):
        if root.gift_card_expiry_period_type is None:
            return None
        return TimePeriod(
            amount=root.gift_card_expiry_period, type=root.gift_card_expiry_period_type
        )


class ExternalAuthentication(graphene.ObjectType):
    id = graphene.String(
        description="ID of external authentication plugin.", required=True
    )
    name = graphene.String(description="Name of external authentication plugin.")


class Limits(graphene.ObjectType):
    channels = graphene.Int()
    orders = graphene.Int()
    product_variants = graphene.Int()
    staff_users = graphene.Int()
    warehouses = graphene.Int()


class LimitInfo(graphene.ObjectType):
    current_usage = graphene.Field(
        Limits,
        required=True,
        description="Defines the current resource usage.",
    )
    allowed_usage = graphene.Field(
        Limits,
        required=True,
        description="Defines the allowed maximum resource usage, null means unlimited.",
    )


class Shop(graphene.ObjectType):
    available_payment_gateways = NonNullList(
        PaymentGateway,
        currency=graphene.Argument(
            graphene.String,
            description=(
                "A currency for which gateways will be returned. "
                f"{DEPRECATED_IN_3X_INPUT} Use `channel` argument instead."
            ),
            required=False,
        ),
        channel=graphene.Argument(
            graphene.String,
            description="Slug of a channel for which the data should be returned.",
            required=False,
        ),
        description="List of available payment gateways.",
        required=True,
    )
    available_external_authentications = NonNullList(
        ExternalAuthentication,
        description="List of available external authentications.",
        required=True,
    )
    available_shipping_methods = NonNullList(
        ShippingMethod,
        channel=graphene.Argument(
            graphene.String,
            description="Slug of a channel for which the data should be returned.",
            required=True,
        ),
        address=graphene.Argument(
            AddressInput,
            description=(
                "Address for which available shipping methods should be returned."
            ),
            required=False,
        ),
        required=False,
        description="Shipping methods that are available for the shop.",
    )
    channel_currencies = PermissionsField(
        NonNullList(graphene.String),
        description=(
            "List of all currencies supported by shop's channels." + ADDED_IN_31
        ),
        required=True,
        permissions=[
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            AuthorizationFilters.AUTHENTICATED_APP,
        ],
    )
    countries = NonNullList(
        CountryDisplay,
        language_code=graphene.Argument(
            LanguageCodeEnum,
            description=(
                "A language code to return the translation for. "
                f"{DEPRECATED_IN_3X_INPUT}"
            ),
        ),
        filter=CountryFilterInput(
            description="Filtering options for countries",
            required=False,
        ),
        description="List of countries available in the shop.",
        required=True,
    )
    default_country = graphene.Field(
        CountryDisplay, description="Shop's default country."
    )
    default_mail_sender_name = PermissionsField(
        graphene.String,
        description="Default shop's email sender's name.",
        permissions=[SitePermissions.MANAGE_SETTINGS],
    )
    default_mail_sender_address = PermissionsField(
        graphene.String,
        description="Default shop's email sender's address.",
        permissions=[SitePermissions.MANAGE_SETTINGS],
    )
    description = graphene.String(description="Shop's description.")
    domain = graphene.Field(Domain, required=True, description="Shop's domain data.")
    languages = NonNullList(
        LanguageDisplay,
        description="List of the shops's supported languages.",
        required=True,
    )
    name = graphene.String(description="Shop's name.", required=True)
    permissions = NonNullList(
        Permission, description="List of available permissions.", required=True
    )
    phone_prefixes = NonNullList(
        graphene.String, description="List of possible phone prefixes.", required=True
    )
    header_text = graphene.String(description="Header text.")
    fulfillment_auto_approve = graphene.Boolean(
        description="Automatically approve all new fulfillments." + ADDED_IN_31,
        required=True,
    )
    fulfillment_allow_unpaid = graphene.Boolean(
        description="Allow to approve fulfillments which are unpaid." + ADDED_IN_31,
        required=True,
    )
    track_inventory_by_default = graphene.Boolean(
        description="Enable inventory tracking."
    )
    default_weight_unit = WeightUnitsEnum(description="Default weight unit.")
    translation = TranslationField(ShopTranslation, type_name="shop", resolver=None)
    automatic_fulfillment_digital_products = PermissionsField(
        graphene.Boolean,
        description="Enable automatic fulfillment for all digital products.",
        permissions=[SitePermissions.MANAGE_SETTINGS],
    )
    reserve_stock_duration_anonymous_user = PermissionsField(
        graphene.Int,
        description=(
            "Default number of minutes stock will be reserved for "
            "anonymous checkout or null when stock reservation is disabled."
            + ADDED_IN_31
        ),
        permissions=[SitePermissions.MANAGE_SETTINGS],
    )
    reserve_stock_duration_authenticated_user = PermissionsField(
        graphene.Int,
        description=(
            "Default number of minutes stock will be reserved for "
            "authenticated checkout or null when stock reservation is disabled."
            + ADDED_IN_31
        ),
        permissions=[SitePermissions.MANAGE_SETTINGS],
    )
    limit_quantity_per_checkout = PermissionsField(
        graphene.Int,
        description=(
            "Default number of maximum line quantity in single checkout "
            "(per single checkout line)." + ADDED_IN_31 + PREVIEW_FEATURE
        ),
        permissions=[SitePermissions.MANAGE_SETTINGS],
    )
    default_digital_max_downloads = PermissionsField(
        graphene.Int,
        description="Default number of max downloads per digital content URL.",
        permissions=[SitePermissions.MANAGE_SETTINGS],
    )
    default_digital_url_valid_days = PermissionsField(
        graphene.Int,
        description="Default number of days which digital content URL will be valid.",
        permissions=[SitePermissions.MANAGE_SETTINGS],
    )
    company_address = graphene.Field(
        Address, description="Company address.", required=False
    )
    customer_set_password_url = graphene.String(
        description="URL of a view where customers can set their password.",
        required=False,
    )
    staff_notification_recipients = PermissionsField(
        NonNullList(StaffNotificationRecipient),
        description="List of staff notification recipients.",
        required=False,
        permissions=[SitePermissions.MANAGE_SETTINGS],
    )
    limits = PermissionsField(
        LimitInfo,
        required=True,
        description="Resource limitations and current usage if any set for a shop",
        permissions=[AuthorizationFilters.AUTHENTICATED_STAFF_USER],
    )
    version = PermissionsField(
        graphene.String,
        description="Saleor API version.",
        required=True,
        permissions=[
            AuthorizationFilters.AUTHENTICATED_STAFF_USER,
            AuthorizationFilters.AUTHENTICATED_APP,
        ],
    )
    schema_version = graphene.String(
        description="Minor Saleor API version." + ADDED_IN_35,
        required=True,
    )

    # deprecated
    include_taxes_in_prices = graphene.Boolean(
        description="Include taxes in prices.",
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use "
            "`Channel.taxConfiguration.pricesEnteredWithTax` to determine whether "
            "prices are entered with tax."
        ),
        required=True,
    )
    display_gross_prices = graphene.Boolean(
        description="Display prices with tax in store.",
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use `Channel.taxConfiguration` to determine "
            "whether to display gross or net prices."
        ),
        required=True,
    )
    charge_taxes_on_shipping = graphene.Boolean(
        description="Charge taxes on shipping.",
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use `ShippingMethodType.taxClass` to determine "
            "whether taxes are calculated for shipping methods; if a tax class is set, "
            "the taxes will be calculated, otherwise no tax rate will be applied."
        ),
        required=True,
    )

    class Meta:
        description = (
            "Represents a shop resource containing general shop data and configuration."
        )

    @staticmethod
    @traced_resolver
    @plugin_manager_promise_callback
    def resolve_available_payment_gateways(
        _, _info, manager, currency: Optional[str] = None, channel: Optional[str] = None
    ):
        return manager.list_payment_gateways(currency=currency, channel_slug=channel)

    @staticmethod
    @traced_resolver
    @plugin_manager_promise_callback
    def resolve_available_external_authentications(_, _info, manager):
        return manager.list_external_authentications(active_only=True)

    @staticmethod
    def resolve_available_shipping_methods(_, info, *, channel, address=None):
        return resolve_available_shipping_methods(
            info, channel_slug=channel, address=address
        )

    @staticmethod
    def resolve_channel_currencies(_, _info):
        return set(
            channel_models.Channel.objects.values_list("currency_code", flat=True)
        )

    @staticmethod
    def resolve_countries(_, _info, **kwargs):
        return resolve_countries(**kwargs)

    @staticmethod
    @load_site_callback
    def resolve_domain(_, _info, site):
        return Domain(
            host=site.domain,
            ssl_enabled=settings.ENABLE_SSL,
            url=build_absolute_uri("/"),
        )

    @staticmethod
    @load_site_callback
    def resolve_description(_, _info, site):
        return site.settings.description

    @staticmethod
    def resolve_languages(_, _info):
        return [
            LanguageDisplay(
                code=LanguageCodeEnum[str_to_enum(language[0])], language=language[1]
            )
            for language in settings.LANGUAGES
        ]

    @staticmethod
    @load_site_callback
    def resolve_name(_, _info, site):
        return site.name

    @staticmethod
    @traced_resolver
    def resolve_permissions(_, _info):
        permissions = get_permissions()
        return format_permissions_for_display(permissions)

    @staticmethod
    def resolve_phone_prefixes(_, _info):
        return list(COUNTRY_CODE_TO_REGION_CODE.keys())

    @staticmethod
    @load_site_callback
    def resolve_header_text(_, _info, site):
        return site.settings.header_text

    @staticmethod
    @load_site_callback
    def resolve_fulfillment_auto_approve(_, _info, site):
        return site.settings.fulfillment_auto_approve

    @staticmethod
    @load_site_callback
    def resolve_fulfillment_allow_unpaid(_, info, site):
        return site.settings.fulfillment_allow_unpaid

    @staticmethod
    @load_site_callback
    def resolve_charge_taxes_on_shipping(_, _info, site):
        return site.settings.charge_taxes_on_shipping

    @staticmethod
    @load_site_callback
    def resolve_track_inventory_by_default(_, _info, site):
        return site.settings.track_inventory_by_default

    @staticmethod
    @load_site_callback
    def resolve_default_weight_unit(_, _info, site):
        return site.settings.default_weight_unit

    @staticmethod
    @traced_resolver
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
    @load_site_callback
    def resolve_default_mail_sender_name(_, _info, site):
        return site.settings.default_mail_sender_name

    @staticmethod
    @load_site_callback
    def resolve_default_mail_sender_address(_, _info, site):
        return site.settings.default_mail_sender_address

    @staticmethod
    @load_site_callback
    def resolve_company_address(_, _info, site):
        return site.settings.company_address

    @staticmethod
    @load_site_callback
    def resolve_customer_set_password_url(_, _info, site):
        return site.settings.customer_set_password_url

    @staticmethod
    @load_site_callback
    def resolve_translation(_, info, site, *, language_code):
        return resolve_translation(site.settings, info, language_code=language_code)

    @staticmethod
    @load_site_callback
    def resolve_automatic_fulfillment_digital_products(_, _info, site):
        return site.settings.automatic_fulfillment_digital_products

    @staticmethod
    @load_site_callback
    def resolve_reserve_stock_duration_anonymous_user(_, _info, site):
        return site.settings.reserve_stock_duration_anonymous_user

    @staticmethod
    @load_site_callback
    def resolve_reserve_stock_duration_authenticated_user(_, _info, site):
        return site.settings.reserve_stock_duration_authenticated_user

    @staticmethod
    @load_site_callback
    def resolve_limit_quantity_per_checkout(_, _info, site):
        return site.settings.limit_quantity_per_checkout

    @staticmethod
    @load_site_callback
    def resolve_default_digital_max_downloads(_, _info, site):
        return site.settings.default_digital_max_downloads

    @staticmethod
    @load_site_callback
    def resolve_default_digital_url_valid_days(_, _info, site):
        return site.settings.default_digital_url_valid_days

    @staticmethod
    def resolve_staff_notification_recipients(_, _info):
        return account_models.StaffNotificationRecipient.objects.all()

    @staticmethod
    def resolve_limits(_, _info):
        return LimitInfo(current_usage=Limits(), allowed_usage=Limits())

    @staticmethod
    def resolve_version(_, _info):
        return __version__

    @staticmethod
    def resolve_schema_version(_, _info):
        major, minor, _ = __version__.split(".", 2)
        return f"{major}.{minor}"

    # deprecated

    @staticmethod
    @load_site_callback
    def resolve_include_taxes_in_prices(_, _info, site):
        return site.settings.include_taxes_in_prices

    @staticmethod
    @load_site_callback
    def resolve_display_gross_prices(_, _info, site):
        return site.settings.display_gross_prices

from email.headerregistry import Address
from email.utils import parseaddr
from functools import reduce
from typing import Final, Optional

from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.sites.requests import RequestSite
from django.core.exceptions import ImproperlyConfigured
from django.core.validators import MaxLengthValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q
from django.http.request import split_domain_port

from ..core import TimePeriodType
from ..core.permissions import SitePermissions
from ..core.units import WeightUnits
from ..core.utils.translations import Translation, TranslationProxy
from ..graphql.core.dataloaders import DataLoader
from . import GiftCardSettingsExpiryType
from .error_codes import SiteErrorCode
from .patch_sites import patch_contrib_sites

patch_contrib_sites()

DEFAULT_LIMIT_QUANTITY_PER_CHECKOUT: Final[int] = 50


def email_sender_name_validators():
    return [
        RegexValidator(
            r"[\n\r]",
            inverse_match=True,
            message="New lines are not allowed.",
            code=SiteErrorCode.FORBIDDEN_CHARACTER.value,
        ),
        MaxLengthValidator(settings.DEFAULT_MAX_EMAIL_DISPLAY_NAME_LENGTH),
    ]


class SiteSettings(models.Model):
    site = models.OneToOneField(Site, related_name="settings", on_delete=models.CASCADE)
    header_text = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=500, blank=True)
    top_menu = models.ForeignKey(
        "menu.Menu", on_delete=models.SET_NULL, related_name="+", blank=True, null=True
    )
    bottom_menu = models.ForeignKey(
        "menu.Menu", on_delete=models.SET_NULL, related_name="+", blank=True, null=True
    )
    include_taxes_in_prices = models.BooleanField(default=True)
    display_gross_prices = models.BooleanField(default=True)
    charge_taxes_on_shipping = models.BooleanField(default=True)
    track_inventory_by_default = models.BooleanField(default=True)
    default_weight_unit = models.CharField(
        max_length=30,
        choices=WeightUnits.CHOICES,  # type: ignore
        default=WeightUnits.KG,  # type: ignore
    )
    automatic_fulfillment_digital_products = models.BooleanField(default=False)
    default_digital_max_downloads = models.IntegerField(blank=True, null=True)
    default_digital_url_valid_days = models.IntegerField(blank=True, null=True)
    company_address = models.ForeignKey(
        "account.Address", blank=True, null=True, on_delete=models.SET_NULL
    )
    # FIXME these values are configurable from email plugin. Not needed to be placed
    # here
    default_mail_sender_name = models.CharField(
        max_length=settings.DEFAULT_MAX_EMAIL_DISPLAY_NAME_LENGTH,
        blank=True,
        default="",
        validators=email_sender_name_validators(),
    )
    default_mail_sender_address = models.EmailField(blank=True, null=True)
    customer_set_password_url = models.CharField(max_length=255, blank=True, null=True)
    automatically_confirm_all_new_orders = models.BooleanField(default=True)
    fulfillment_auto_approve = models.BooleanField(default=True)
    fulfillment_allow_unpaid = models.BooleanField(default=True)

    # Duration in minutes
    reserve_stock_duration_anonymous_user = models.IntegerField(blank=True, null=True)
    reserve_stock_duration_authenticated_user = models.IntegerField(
        blank=True, null=True
    )

    limit_quantity_per_checkout = models.IntegerField(
        blank=True,
        null=True,
        default=DEFAULT_LIMIT_QUANTITY_PER_CHECKOUT,
        validators=[MinValueValidator(1)],
    )

    # gift card settings
    gift_card_expiry_type = models.CharField(
        max_length=32,
        choices=GiftCardSettingsExpiryType.CHOICES,
        default=GiftCardSettingsExpiryType.NEVER_EXPIRE,
    )
    gift_card_expiry_period_type = models.CharField(
        max_length=32, choices=TimePeriodType.CHOICES, null=True, blank=True
    )
    gift_card_expiry_period = models.PositiveIntegerField(null=True, blank=True)
    automatically_fulfill_non_shippable_gift_card = models.BooleanField(default=True)

    translated = TranslationProxy()

    class Meta:
        permissions = (
            (SitePermissions.MANAGE_SETTINGS.codename, "Manage settings."),
            (SitePermissions.MANAGE_TRANSLATIONS.codename, "Manage translations."),
        )

    def __str__(self):
        return self.site.name

    @property
    def default_from_email(self) -> str:
        sender_name: str = self.default_mail_sender_name
        sender_address: Optional[str] = self.default_mail_sender_address

        if not sender_address:
            sender_address = settings.DEFAULT_FROM_EMAIL

            if not sender_address:
                raise ImproperlyConfigured("No sender email address has been set-up")

            sender_name, sender_address = parseaddr(sender_address)

        # Note: we only want to format the address in accordance to RFC 5322
        # but our job is not to sanitize the values. The sanitized value, encoding, etc.
        # will depend on the email backend being used.
        #
        # Refer to email.header.Header and django.core.mail.message.sanitize_address.
        value = str(Address(sender_name, addr_spec=sender_address))
        return value


class SiteSettingsTranslation(Translation):
    site_settings = models.ForeignKey(
        SiteSettings, related_name="translations", on_delete=models.CASCADE
    )
    header_text = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=500, blank=True)

    class Meta:
        unique_together = (("language_code", "site_settings"),)

    def __repr__(self):
        class_ = type(self)
        return "%s(pk=%r, site_settings_pk=%r)" % (
            class_.__name__,
            self.pk,
            self.site_settings_id,
        )

    def __str__(self):
        return self.site_settings.site.name

    def get_translated_object_id(self):
        return "Shop", self.site_settings_id

    def get_translated_keys(self):
        return {
            "header_text": self.header_text,
            "description": self.description,
        }


class SiteByIdLoader(DataLoader):
    context_key = "site_by_id"

    def batch_load(self, keys):
        sites_mapped = Site.objects.using(self.database_connection_name).in_bulk(keys)
        return [sites_mapped.get(site_id) for site_id in keys]


class SiteByHostLoader(DataLoader):
    context_key = "site_by_host"

    def batch_load(self, keys):
        sites_mapped = Site.objects.using(self.database_connection_name).in_bulk(keys)
        # simulate nonexisting `domain__iexact__in`
        q_list = map(lambda k: Q(domain__iexact=k), keys)
        q_list = reduce(lambda a, b: a | b, q_list)
        sites = Site.objects.using(self.database_connection_name).filter(q_list)
        sites_mapped = {s.domain.lower(): s for s in sites}
        return [sites_mapped.get(host.lower()) for host in keys]


def load_current_site(request):
    from django.conf import settings

    if getattr(settings, "SITE_ID", ""):
        site_id = settings.SITE_ID
        return SiteByIdLoader(request).load(site_id).get()

    host = request.get_host()
    site = SiteByHostLoader(request).load(host).get()

    if site is None:
        domain, port = split_domain_port(host)
        site = SiteByHostLoader(request).load(domain).get()

    if site is None:
        raise ImproperlyConfigured(
            'You\'re using the Django "sites framework" without having '
            "set the SITE_ID setting. Create a site in your database and "
            "set the SITE_ID setting."
        )
    else:
        # Populate the other loader for free
        SiteByIdLoader(request).prime(site.id, site)
    return site


def load_site(request, site_id=None):
    if site_id is None:
        return load_current_site(request)
    return SiteByIdLoader(request).load(site_id).get() or RequestSite(request)

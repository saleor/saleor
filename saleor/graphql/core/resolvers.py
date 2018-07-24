from django.conf import settings
from django_countries import countries
from phonenumbers import COUNTRY_CODE_TO_REGION_CODE

from ...core.permissions import get_permissions
from ..utils import format_permissions_for_display
from .types import CountryDisplay, LanguageDisplay, Shop, Domain


def resolve_shop(root, info, *args, **kwargs):
    site = info.context.site
    return Shop(
        countries=resolve_countries(info),
        currencies=settings.AVAILABLE_CURRENCIES,
        domain=resolve_domain(info, site),
        default_currency=settings.DEFAULT_CURRENCY,
        languages=resolve_languages(info),
        name=site.name,
        permissions=resolve_permissions(info),
        phone_prefixes=resolve_phone_prefixes(info))


def resolve_domain(info, site):
    return Domain(
        host=site.domain,
        ssl_enabled=settings.ENABLE_SSL,
        url=info.context.build_absolute_uri('/'))


def resolve_phone_prefixes(info):
    return list(COUNTRY_CODE_TO_REGION_CODE.keys())


def resolve_countries(info):
    return [
        CountryDisplay(code=country[0], country=country[1])
        for country in countries]


def resolve_languages(info):
    return [
        LanguageDisplay(code=language[0], language=language[1])
        for language in settings.LANGUAGES]


def resolve_permissions(info):
    permissions = get_permissions()
    return format_permissions_for_display(permissions)

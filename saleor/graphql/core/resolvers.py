from django.conf import settings
from phonenumbers import COUNTRY_CODE_TO_REGION_CODE

from ...core.permissions import get_permissions
from ..utils import format_permissions_for_display
from .types import LanguageDisplay, Shop


def resolve_shop(root, info):
    permissions = get_permissions()
    permissions = format_permissions_for_display(permissions)
    languages = settings.LANGUAGES
    languages = [LanguageDisplay(
        code=language[0], language=language[1]) for language in languages]
    phone_prefixes = list(COUNTRY_CODE_TO_REGION_CODE.keys())
    return Shop(
        permissions=permissions,
        languages=languages,
        phone_prefixes=phone_prefixes)

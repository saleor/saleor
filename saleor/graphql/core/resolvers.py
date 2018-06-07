from .types import Shop
from ...core.permissions import get_permissions
from .types import LanguageDisplay
from django.conf import settings
from ..utils import format_permissions_for_display

def resolve_shop(root, info):
    permissions = get_permissions()
    permissions = format_permissions_for_display(permissions)
    languages = settings.LANGUAGES
    languages = [LanguageDisplay(
        code=language[0], language=language[1]) for language in languages]
    return Shop(permissions=permissions, languages=languages)

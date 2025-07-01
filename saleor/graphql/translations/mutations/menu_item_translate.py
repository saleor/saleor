import graphene

from ....menu import models as menu_models
from ....permission.enums import SitePermissions
from ...core import ResolveInfo
from ...core.context import ChannelContext
from ...core.enums import LanguageCodeEnum
from ...core.types import TranslationError
from ...menu.types import MenuItem
from .utils import BaseTranslateMutation, NameTranslationInput


class MenuItemTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description="MenuItem ID or MenuItemTranslatableContent ID."
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = NameTranslationInput(
            required=True,
            description="Fields required to update menu item translations.",
        )

    class Meta:
        description = "Creates/updates translations for a menu item."
        model = menu_models.MenuItem
        object_type = MenuItem
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, root, info: ResolveInfo, /, *, id, input, language_code
    ):
        response = super().perform_mutation(
            root, info, id=id, input=input, language_code=language_code
        )
        instance = ChannelContext(node=response.menuItem, channel_slug=None)
        return cls(**{cls._meta.return_field_name: instance})

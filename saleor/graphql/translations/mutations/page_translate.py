import graphene

from ....page import models as page_models
from ....permission.enums import SitePermissions
from ...core.descriptions import RICH_CONTENT
from ...core.enums import LanguageCodeEnum
from ...core.fields import JSONString
from ...core.types import TranslationError
from .. import types as translation_types
from .utils import BaseTranslateMutation, SeoTranslationInput


class PageTranslationInput(SeoTranslationInput):
    title = graphene.String()
    content = JSONString(description="Translated page content." + RICH_CONTENT)


class PageTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description="Page ID or PageTranslatableContent ID."
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = PageTranslationInput(
            required=True, description="Fields required to update page translations."
        )

    class Meta:
        description = "Creates/updates translations for a page."
        model = page_models.Page
        # Note: `PageTranslate` is only mutation that returns "TranslatableContent"
        object_type = translation_types.PageTranslatableContent
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

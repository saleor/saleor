import graphene

from ....discount import models as discount_models
from ....permission.enums import SitePermissions
from ...core.descriptions import ADDED_IN_317, RICH_CONTENT
from ...core.enums import LanguageCodeEnum
from ...core.scalars import JSON
from ...core.types import TranslationError
from ...discount.types import Promotion
from .utils import BaseTranslateMutation, NameTranslationInput


class PromotionTranslationInput(NameTranslationInput):
    description = JSON(description="Translated promotion description." + RICH_CONTENT)


class PromotionTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(
            required=True,
            description="Promotion ID or PromotionTranslatableContent ID.",
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = PromotionTranslationInput(
            required=True,
            description="Fields required to update promotion translations.",
        )

    class Meta:
        description = "Creates/updates translations for a promotion." + ADDED_IN_317
        model = discount_models.Promotion
        object_type = Promotion
        error_type_class = TranslationError
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

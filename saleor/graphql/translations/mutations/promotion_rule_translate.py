import graphene

from ....discount import models as discount_models
from ....permission.enums import SitePermissions
from ...core.descriptions import ADDED_IN_315, RICH_CONTENT
from ...core.enums import LanguageCodeEnum
from ...core.scalars import JSON
from ...core.types import TranslationError
from ...discount.types import PromotionRule
from .utils import BaseTranslateMutation, NameTranslationInput


class PromotionRuleTranslationInput(NameTranslationInput):
    description = JSON(description="Translated promotion description." + RICH_CONTENT)


class PromotionRuleTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(
            required=True,
            description="PromotionRule ID or PromotionRuleTranslatableContent ID.",
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = PromotionRuleTranslationInput(
            required=True,
            description="Fields required to update promotion rule translations.",
        )

    class Meta:
        description = (
            "Creates/updates translations for a promotion rule." + ADDED_IN_315
        )
        model = discount_models.PromotionRule
        object_type = PromotionRule
        error_type_class = TranslationError
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

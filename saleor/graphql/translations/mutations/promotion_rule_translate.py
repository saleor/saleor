import graphene

from ....discount import models as discount_models
from ....permission.enums import SitePermissions
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_317, RICH_CONTENT
from ...core.enums import LanguageCodeEnum
from ...core.scalars import JSON
from ...core.types import TranslationError
from ...discount.mutations.utils import clear_promotion_old_sale_id
from ...discount.types import PromotionRule
from ...plugins.dataloaders import get_plugin_manager_promise
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
            "Creates/updates translations for a promotion rule." + ADDED_IN_317
        )
        model = discount_models.PromotionRule
        object_type = PromotionRule
        error_type_class = TranslationError
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, input, language_code
    ):
        node_id, model_type = cls.clean_node_id(id)
        instance = cls.get_node_or_error(info, node_id, only_type=model_type)
        cls.validate_input(input)

        input = cls.pre_update_or_create(instance, input)
        translation, created = instance.translations.update_or_create(
            language_code=language_code, defaults=input
        )
        clear_promotion_old_sale_id(instance.promotion, save=True)

        manager = get_plugin_manager_promise(info.context).get()
        if created:
            cls.call_event(manager.translation_created, translation)
        else:
            cls.call_event(manager.translation_updated, translation)

        return cls(**{cls._meta.return_field_name: instance})

import graphene

from ....permission.enums import SitePermissions
from ....product import models as product_models
from ...core.descriptions import ADDED_IN_323
from ...core.enums import LanguageCodeEnum
from ...core.types import TranslationError
from ...product.types import Category
from .utils import BaseTranslateMutationWithSlug, TranslationInput


class CategoryTranslate(BaseTranslateMutationWithSlug):
    class Arguments:
        id = graphene.ID(
            required=False,
            description="Category ID or CategoryTranslatableContent ID.",
        )
        external_reference = graphene.String(
            required=False,
            description=f"External ID of a category to translate.{ADDED_IN_323}",
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = TranslationInput(
            required=True,
            description="Fields required to update category translations.",
        )

    class Meta:
        description = "Creates/updates translations for a category."
        model = product_models.Category
        object_type = Category
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

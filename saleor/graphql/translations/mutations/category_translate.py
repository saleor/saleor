import graphene

from ....permission.enums import SitePermissions
from ....product import models as product_models
from ...core.descriptions import ADDED_IN_323, RICH_CONTENT
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.enums import LanguageCodeEnum
from ...core.fields import JSONString
from ...core.types import BaseInputObjectType, TranslationError
from ...product.types import Category
from .utils import BaseTranslateMutationWithSlug


class CategoryTranslationInput(BaseInputObjectType):
    name = graphene.String(description="Translated category name." + ADDED_IN_323)
    slug = graphene.String(description="Translated category slug." + ADDED_IN_323)
    seo_title = graphene.String(
        description="Translated category SEO title." + ADDED_IN_323
    )
    seo_description = graphene.String(
        description="Translated category SEO description." + ADDED_IN_323
    )
    description = JSONString(
        description="Translated category description." + RICH_CONTENT + ADDED_IN_323
    )
    background_image_alt = graphene.String(
        description="Translated category background image alt text." + ADDED_IN_323
    )

    class Meta:
        description = "Fields required to translate a category." + ADDED_IN_323
        doc_category = DOC_CATEGORY_PRODUCTS


class CategoryTranslate(BaseTranslateMutationWithSlug):
    class Arguments:
        id = graphene.ID(
            required=True,
            description="Category ID or CategoryTranslatableContent ID.",
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = CategoryTranslationInput(
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

    @classmethod
    def pre_update_or_create(cls, instance, input_data, language_code):
        input_data = super().pre_update_or_create(instance, input_data, language_code)
        if input_data.get("background_image_alt") is None:
            input_data.pop("background_image_alt", None)
        return input_data

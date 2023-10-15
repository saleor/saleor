import graphene

from ....attribute import models as attribute_models
from ....permission.enums import SitePermissions
from ...attribute.types import Attribute
from ...core.enums import LanguageCodeEnum
from ...core.types import TranslationError
from .utils import BaseTranslateMutation, NameTranslationInput


class AttributeTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(
            required=True,
            description="Attribute ID or AttributeTranslatableContent ID.",
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = NameTranslationInput(
            required=True,
            description="Fields required to update attribute translations.",
        )

    class Meta:
        description = "Creates/updates translations for an attribute."
        model = attribute_models.Attribute
        object_type = Attribute
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

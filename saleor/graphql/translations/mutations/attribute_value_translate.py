import graphene
from django.template.defaultfilters import truncatechars

from ....attribute import AttributeInputType
from ....attribute import models as attribute_models
from ....core.utils.editorjs import clean_editor_js
from ....permission.enums import SitePermissions
from ...attribute.types import AttributeValue
from ...core.descriptions import RICH_CONTENT
from ...core.enums import LanguageCodeEnum
from ...core.fields import JSONString
from ...core.types import TranslationError
from .utils import BaseTranslateMutation, NameTranslationInput


class AttributeValueTranslationInput(NameTranslationInput):
    rich_text = JSONString(description="Translated text." + RICH_CONTENT)
    plain_text = graphene.String(description="Translated text.")


class AttributeValueTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(
            required=True,
            description="AttributeValue ID or AttributeValueTranslatableContent ID.",
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = AttributeValueTranslationInput(required=True)

    class Meta:
        description = "Creates/updates translations for an attribute value."
        model = attribute_models.AttributeValue
        object_type = AttributeValue
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

    @classmethod
    def pre_update_or_create(cls, instance, input_data):
        if "name" not in input_data.keys() or input_data["name"] is None:
            if instance.attribute.input_type == AttributeInputType.RICH_TEXT:
                input_data["name"] = truncatechars(
                    clean_editor_js(input_data["rich_text"], to_string=True), 250
                )
            elif instance.attribute.input_type == AttributeInputType.PLAIN_TEXT:
                input_data["name"] = truncatechars(input_data["plain_text"], 250)
        return input_data

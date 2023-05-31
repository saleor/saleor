import graphene
from django.core.exceptions import ValidationError
from django.template.defaultfilters import truncatechars

from ....attribute import AttributeInputType, models
from ....core.utils.editorjs import clean_editor_js
from ....permission.enums import SitePermissions
from ...attribute.types import AttributeValueTranslation
from ...core.descriptions import ADDED_IN_314, PREVIEW_FEATURE
from ...core.doc_category import DOC_CATEGORY_ATTRIBUTES
from ...core.enums import LanguageCodeEnum, TranslationErrorCode
from ...core.types import (
    BaseInputObjectType,
    BaseObjectType,
    NonNullList,
    TranslationBulkError,
)
from ...core.validators import validate_one_of_args_is_in_mutation
from .attribute_value_translate import AttributeValueTranslationInput
from .utils import BaseBulkTranslateMutation


class AttributeValueBulkTranslateResult(BaseObjectType):
    translation = graphene.Field(
        AttributeValueTranslation, description="Attribute value translation data."
    )
    errors = NonNullList(
        TranslationBulkError,
        required=False,
        description="List of errors occurred on translation attempt.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES


class AttributeValueBulkTranslateInput(BaseInputObjectType):
    id = graphene.ID(
        required=False,
        description="Attribute value ID.",
    )
    external_reference = graphene.String(
        required=False,
        description="External reference of an attribute value.",
    )
    language_code = LanguageCodeEnum(
        required=True, description="Translation language code."
    )
    translation_fields = AttributeValueTranslationInput(
        required=True,
        description="Translation fields.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES


class AttributeValueBulkTranslate(BaseBulkTranslateMutation):
    count = graphene.Int(
        required=True,
        description="Returns how many translations were created/updated.",
    )
    results = NonNullList(
        AttributeValueBulkTranslateResult,
        required=True,
        default_value=[],
        description="List of the translations.",
    )

    class Arguments(BaseBulkTranslateMutation.Arguments):
        translations = NonNullList(
            AttributeValueBulkTranslateInput,
            required=True,
            description="List of attribute values translations.",
        )

    class Meta:
        description = (
            "Creates/updates translations for attributes values."
            + ADDED_IN_314
            + PREVIEW_FEATURE
        )
        base_model = models.AttributeValue
        translation_model = models.AttributeValueTranslation
        translation_fields = ["name", "rich_text", "plain_text"]
        base_model_relation_field = "attribute_value"
        result_type = AttributeValueBulkTranslateResult
        error_type_class = TranslationBulkError
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @classmethod
    def clean_translations(cls, data_inputs, index_error_map):
        cleaned_inputs_map: dict = {}

        for index, data in enumerate(data_inputs):
            id = data.get("id")
            external_ref = data.get("external_reference")

            try:
                validate_one_of_args_is_in_mutation(
                    "id",
                    id,
                    "external_reference",
                    external_ref,
                    use_camel_case=True,
                )
            except ValidationError as exc:
                index_error_map[index].append(
                    TranslationBulkError(
                        message=exc.message,
                        code=TranslationErrorCode.INVALID.value,
                    )
                )
                cleaned_inputs_map[index] = None
                continue

            if id:
                data["id"] = graphene.Node.from_global_id(id)[1]
            cleaned_inputs_map[index] = data

        return cleaned_inputs_map

    @classmethod
    def pre_update_or_create(cls, instance, input_data):
        if "name" not in input_data.keys() or input_data["name"] is None:
            if instance.attribute.input_type == AttributeInputType.RICH_TEXT:
                input_data["name"] = truncatechars(
                    clean_editor_js(input_data["rich_text"], to_string=True), 100
                )
            elif instance.attribute.input_type == AttributeInputType.PLAIN_TEXT:
                input_data["name"] = truncatechars(input_data["plain_text"], 100)
        return input_data

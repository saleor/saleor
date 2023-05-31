import graphene
from django.core.exceptions import ValidationError

from ....attribute import models
from ....permission.enums import SitePermissions
from ...attribute.types import AttributeTranslation
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
from .utils import BaseBulkTranslateMutation, NameTranslationInput


class AttributeBulkTranslateResult(BaseObjectType):
    translation = graphene.Field(
        AttributeTranslation, description="Attribute translation data."
    )
    errors = NonNullList(
        TranslationBulkError,
        required=False,
        description="List of errors occurred on translation attempt.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES


class AttributeBulkTranslateInput(BaseInputObjectType):
    id = graphene.ID(
        required=False,
        description="Attribute ID.",
    )
    external_reference = graphene.String(
        required=False,
        description="External reference of an attribute.",
    )
    language_code = LanguageCodeEnum(
        required=True, description="Translation language code."
    )
    translation_fields = NameTranslationInput(
        required=True,
        description="Translation fields.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES


class AttributeBulkTranslate(BaseBulkTranslateMutation):
    results = NonNullList(
        AttributeBulkTranslateResult,
        required=True,
        default_value=[],
        description="List of the translations.",
    )

    class Arguments(BaseBulkTranslateMutation.Arguments):
        translations = NonNullList(
            AttributeBulkTranslateInput,
            required=True,
            description="List of attributes translations.",
        )

    class Meta:
        description = (
            "Creates/updates translations for attributes."
            + ADDED_IN_314
            + PREVIEW_FEATURE
        )
        base_model = models.Attribute
        translation_model = models.AttributeTranslation
        translation_fields = ["name"]
        base_model_relation_field = "attribute"
        result_type = AttributeBulkTranslateResult
        error_type_class = TranslationBulkError
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

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

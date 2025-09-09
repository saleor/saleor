import graphene
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from ....attribute import models
from ....permission.enums import SitePermissions
from ...attribute.types import AttributeTranslation
from ...core.doc_category import DOC_CATEGORY_ATTRIBUTES
from ...core.enums import AttributeTranslateErrorCode, LanguageCodeEnum
from ...core.types import AttributeBulkTranslateError, NonNullList
from ...core.utils import from_global_id_or_error
from ...core.validators import validate_one_of_args_is_in_mutation
from ...directives import doc
from .utils import BaseBulkTranslateMutation, NameTranslationInput


@doc(category=DOC_CATEGORY_ATTRIBUTES)
class AttributeBulkTranslateResult(graphene.ObjectType):
    translation = graphene.Field(
        AttributeTranslation, description="Attribute translation data."
    )
    errors = NonNullList(
        AttributeBulkTranslateError,
        required=False,
        description="List of errors occurred on translation attempt.",
    )


@doc(category=DOC_CATEGORY_ATTRIBUTES)
class AttributeBulkTranslateInput(graphene.InputObjectType):
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


@doc(category=DOC_CATEGORY_ATTRIBUTES)
class AttributeBulkTranslate(BaseBulkTranslateMutation):
    results = NonNullList(
        AttributeBulkTranslateResult,
        required=True,
        default_value=(),
        description="List of the translations.",
    )

    class Arguments(BaseBulkTranslateMutation.Arguments):
        translations = NonNullList(
            AttributeBulkTranslateInput,
            required=True,
            description="List of attributes translations.",
        )

    class Meta:
        description = "Creates/updates translations for attributes."
        base_model = models.Attribute
        translation_model = models.AttributeTranslation
        translation_fields = ["name"]
        base_model_relation_field = "attribute"
        result_type = AttributeBulkTranslateResult
        error_type_class = AttributeBulkTranslateError
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

    @classmethod
    def clean_translations(cls, data_inputs, index_error_map):
        cleaned_inputs_map: dict = {}

        for index, data in enumerate(data_inputs):
            global_id = data.get("id")
            external_ref = data.get("external_reference")

            try:
                validate_one_of_args_is_in_mutation(
                    "id",
                    global_id,
                    "external_reference",
                    external_ref,
                    use_camel_case=True,
                )
            except ValidationError as exc:
                index_error_map[index].append(
                    AttributeBulkTranslateError(
                        message=exc.message,
                        code=AttributeTranslateErrorCode.INVALID.value,
                    )
                )
                cleaned_inputs_map[index] = None
                continue

            if global_id:
                try:
                    obj_type, id = from_global_id_or_error(
                        global_id, only_type="Attribute"
                    )
                except GraphQLError as exc:
                    index_error_map[index].append(
                        AttributeBulkTranslateError(
                            message=str(exc),
                            code=AttributeTranslateErrorCode.INVALID.value,
                        )
                    )
                    cleaned_inputs_map[index] = None
                    continue
                data["id"] = id

            cleaned_inputs_map[index] = data

        return cleaned_inputs_map

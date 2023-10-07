import graphene
from django.core.exceptions import ValidationError
from graphql.error import GraphQLError

from ....permission.enums import SitePermissions
from ....product import models
from ...core.descriptions import ADDED_IN_315, PREVIEW_FEATURE
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.enums import LanguageCodeEnum, ProductVariantTranslateErrorCode
from ...core.types import (
    BaseInputObjectType,
    BaseObjectType,
    NonNullList,
    ProductVariantBulkTranslateError,
)
from ...core.utils import (
    WebhookEventAsyncType,
    WebhookEventInfo,
    from_global_id_or_error,
)
from ...core.validators import validate_one_of_args_is_in_mutation
from ...translations.types import ProductVariantTranslation
from .utils import BaseBulkTranslateMutation, NameTranslationInput


class ProductVariantBulkTranslateResult(BaseObjectType):
    translation = graphene.Field(
        ProductVariantTranslation, description="Product variant translation data."
    )
    errors = NonNullList(
        ProductVariantBulkTranslateError,
        required=False,
        description="List of errors occurred on translation attempt.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductVariantBulkTranslateInput(BaseInputObjectType):
    id = graphene.ID(
        required=False,
        description="Product variant ID.",
    )
    external_reference = graphene.String(
        required=False,
        description="External reference of a product variant.",
    )
    language_code = LanguageCodeEnum(
        required=True, description="Translation language code."
    )
    translation_fields = NameTranslationInput(
        required=True,
        description="Translation fields.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductVariantBulkTranslate(BaseBulkTranslateMutation):
    results = NonNullList(
        ProductVariantBulkTranslateResult,
        required=True,
        default_value=[],
        description="List of the translations.",
    )

    class Arguments(BaseBulkTranslateMutation.Arguments):
        translations = NonNullList(
            ProductVariantBulkTranslateInput,
            required=True,
            description="List of products variants translations.",
        )

    class Meta:
        description = (
            "Creates/updates translations for products variants."
            + ADDED_IN_315
            + PREVIEW_FEATURE
        )
        base_model = models.ProductVariant
        translation_model = models.ProductVariantTranslation
        translation_fields = ["name"]
        base_model_relation_field = "product_variant"
        result_type = ProductVariantBulkTranslateResult
        error_type_class = ProductVariantBulkTranslateError
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.TRANSLATION_CREATED,
                description="A translation was created.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.TRANSLATION_UPDATED,
                description="A translation was updated.",
            ),
        ]

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
                    ProductVariantBulkTranslateError(
                        message=exc.message,
                        code=ProductVariantTranslateErrorCode.INVALID.value,
                    )
                )
                cleaned_inputs_map[index] = None
                continue

            if global_id:
                try:
                    obj_type, id = from_global_id_or_error(
                        global_id, only_type="ProductVariant"
                    )
                except GraphQLError as exc:
                    index_error_map[index].append(
                        ProductVariantBulkTranslateError(
                            message=str(exc),
                            code=ProductVariantTranslateErrorCode.INVALID.value,
                        )
                    )
                    cleaned_inputs_map[index] = None
                    continue
                data["id"] = id

            cleaned_inputs_map[index] = data
        return cleaned_inputs_map

import graphene
from django.core.exceptions import ValidationError
from graphql.error import GraphQLError

from ....permission.enums import SitePermissions
from ....product import models
from ...core.descriptions import ADDED_IN_315, PREVIEW_FEATURE
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.enums import LanguageCodeEnum, ProductTranslateErrorCode
from ...core.types import (
    BaseInputObjectType,
    BaseObjectType,
    NonNullList,
    ProductBulkTranslateError,
)
from ...core.utils import (
    WebhookEventAsyncType,
    WebhookEventInfo,
    from_global_id_or_error,
)
from ...core.validators import validate_one_of_args_is_in_mutation
from ...translations.types import ProductTranslation
from .utils import BaseBulkTranslateMutation, TranslationInput


class ProductBulkTranslateResult(BaseObjectType):
    translation = graphene.Field(
        ProductTranslation, description="Product translation data."
    )
    errors = NonNullList(
        ProductBulkTranslateError,
        required=False,
        description="List of errors occurred on translation attempt.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductBulkTranslateInput(BaseInputObjectType):
    id = graphene.ID(
        required=False,
        description="Product ID.",
    )
    external_reference = graphene.String(
        required=False,
        description="External reference of an product.",
    )
    language_code = LanguageCodeEnum(
        required=True, description="Translation language code."
    )
    translation_fields = TranslationInput(
        required=True,
        description="Translation fields.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductBulkTranslate(BaseBulkTranslateMutation):
    results = NonNullList(
        ProductBulkTranslateResult,
        required=True,
        default_value=[],
        description="List of the translations.",
    )

    class Arguments(BaseBulkTranslateMutation.Arguments):
        translations = NonNullList(
            ProductBulkTranslateInput,
            required=True,
            description="List of product translations.",
        )

    class Meta:
        description = (
            "Creates/updates translations for products."
            + ADDED_IN_315
            + PREVIEW_FEATURE
        )
        base_model = models.Product
        translation_model = models.ProductTranslation
        translation_fields = ["name", "description", "seo_description", "seo_title"]
        base_model_relation_field = "product"
        result_type = ProductBulkTranslateResult
        error_type_class = ProductBulkTranslateError
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.TRANSLATION_CREATED,
                description="Called when a translation was created.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.TRANSLATION_UPDATED,
                description="Called when a translation was updated.",
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
                    ProductBulkTranslateError(
                        message=exc.message,
                        code=ProductTranslateErrorCode.INVALID.value,
                    )
                )
                cleaned_inputs_map[index] = None
                continue

            if global_id:
                try:
                    obj_type, id = from_global_id_or_error(
                        global_id, only_type="Product"
                    )
                except GraphQLError as exc:
                    index_error_map[index].append(
                        ProductBulkTranslateError(
                            message=str(exc),
                            code=ProductTranslateErrorCode.INVALID.value,
                        )
                    )
                    cleaned_inputs_map[index] = None
                    continue
                data["id"] = id

            cleaned_inputs_map[index] = data
        return cleaned_inputs_map

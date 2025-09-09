import graphene
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from ....permission.enums import SitePermissions
from ....product import models
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.enums import LanguageCodeEnum, ProductTranslateErrorCode
from ...core.types import NonNullList, ProductBulkTranslateError
from ...core.utils import WebhookEventAsyncType, from_global_id_or_error
from ...core.validators import validate_one_of_args_is_in_mutation
from ...directives import doc, webhook_events
from ...translations.types import ProductTranslation
from .utils import BaseBulkTranslateMutation, TranslationInput


@doc(category=DOC_CATEGORY_PRODUCTS)
class ProductBulkTranslateResult(graphene.ObjectType):
    translation = graphene.Field(
        ProductTranslation, description="Product translation data."
    )
    errors = NonNullList(
        ProductBulkTranslateError,
        required=False,
        description="List of errors occurred on translation attempt.",
    )


@doc(category=DOC_CATEGORY_PRODUCTS)
class ProductBulkTranslateInput(graphene.InputObjectType):
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


@doc(category=DOC_CATEGORY_PRODUCTS)
@webhook_events(
    async_events={
        WebhookEventAsyncType.TRANSLATION_CREATED,
        WebhookEventAsyncType.TRANSLATION_UPDATED,
    }
)
class ProductBulkTranslate(BaseBulkTranslateMutation):
    results = NonNullList(
        ProductBulkTranslateResult,
        required=True,
        default_value=(),
        description="List of the translations.",
    )

    class Arguments(BaseBulkTranslateMutation.Arguments):
        translations = NonNullList(
            ProductBulkTranslateInput,
            required=True,
            description="List of product translations.",
        )

    class Meta:
        description = "Creates/updates translations for products."
        base_model = models.Product
        translation_model = models.ProductTranslation
        translation_fields = ["name", "description", "seo_description", "seo_title"]
        base_model_relation_field = "product"
        result_type = ProductBulkTranslateResult
        error_type_class = ProductBulkTranslateError
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

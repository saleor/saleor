import graphene

from ....permission.enums import SitePermissions
from ....product import models as product_models
from ...core.descriptions import ADDED_IN_323
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.enums import LanguageCodeEnum, ProductMediaTranslateErrorCode
from ...core.types import BaseInputObjectType, Error
from ...product.types import ProductMedia
from .utils import BaseTranslateMutation


class ProductMediaTranslateError(Error):
    code = ProductMediaTranslateErrorCode(
        description="The error code." + ADDED_IN_323,
        required=True,
    )

    class Meta:
        description = (
            "Represents an error in product media translation input." + ADDED_IN_323
        )
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductMediaTranslationInput(BaseInputObjectType):
    alt = graphene.String(
        description="Translated product media alt text." + ADDED_IN_323
    )

    class Meta:
        description = "Fields required to translate product media." + ADDED_IN_323
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductMediaTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(
            required=True,
            description=(
                "ProductMedia ID or ProductMediaTranslatableContent ID." + ADDED_IN_323
            ),
        )
        language_code = graphene.Argument(
            LanguageCodeEnum,
            required=True,
            description="Translation language code." + ADDED_IN_323,
        )
        input = ProductMediaTranslationInput(
            required=True,
            description="Fields required to update product media translations."
            + ADDED_IN_323,
        )

    class Meta:
        description = "Creates or updates a product media translation." + ADDED_IN_323
        model = product_models.ProductMedia
        object_type = ProductMedia
        error_type_class = ProductMediaTranslateError
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

    @classmethod
    def pre_update_or_create(cls, instance, input_data, language_code):
        if input_data.get("alt") is None:
            input_data.pop("alt", None)
        return input_data

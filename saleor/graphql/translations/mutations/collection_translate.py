import graphene

from ....permission.enums import SitePermissions
from ....product import models as product_models
from ...core import ResolveInfo
from ...core.context import ChannelContext
from ...core.descriptions import ADDED_IN_323, RICH_CONTENT
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.enums import LanguageCodeEnum
from ...core.fields import JSONString
from ...core.types import BaseInputObjectType, TranslationError
from ...product.types import Collection
from .utils import BaseTranslateMutationWithSlug


class CollectionTranslationInput(BaseInputObjectType):
    name = graphene.String(description="Translated collection name." + ADDED_IN_323)
    slug = graphene.String(description="Translated collection slug." + ADDED_IN_323)
    seo_title = graphene.String(
        description="Translated collection SEO title." + ADDED_IN_323
    )
    seo_description = graphene.String(
        description="Translated collection SEO description." + ADDED_IN_323
    )
    description = JSONString(
        description="Translated collection description." + RICH_CONTENT + ADDED_IN_323
    )
    background_image_alt = graphene.String(
        description="Translated collection background image alt text." + ADDED_IN_323
    )

    class Meta:
        description = "Fields required to translate a collection." + ADDED_IN_323
        doc_category = DOC_CATEGORY_PRODUCTS


class CollectionTranslate(BaseTranslateMutationWithSlug):
    class Arguments:
        id = graphene.ID(
            required=True,
            description="Collection ID or CollectionTranslatableContent ID.",
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = CollectionTranslationInput(
            required=True,
            description="Fields required to update collection translations.",
        )

    class Meta:
        description = "Creates/updates translations for a collection."
        model = product_models.Collection
        object_type = Collection
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

    @classmethod
    def pre_update_or_create(cls, instance, input_data, language_code):
        input_data = super().pre_update_or_create(instance, input_data, language_code)
        if input_data.get("background_image_alt") is None:
            input_data.pop("background_image_alt", None)
        return input_data

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, root, info: ResolveInfo, /, *, id, input, language_code
    ):
        response = super().perform_mutation(
            root, info, id=id, input=input, language_code=language_code
        )
        instance = ChannelContext(node=response.collection, channel_slug=None)
        return cls(**{cls._meta.return_field_name: instance})

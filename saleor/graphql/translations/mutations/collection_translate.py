import graphene

from ....permission.enums import SitePermissions
from ....product import models as product_models
from ...core import ResolveInfo
from ...core.context import ChannelContext
from ...core.descriptions import ADDED_IN_323
from ...core.enums import LanguageCodeEnum
from ...core.types import TranslationError
from ...product.types import Collection
from .utils import BaseTranslateMutationWithSlug, TranslationInput


class CollectionTranslate(BaseTranslateMutationWithSlug):
    class Arguments:
        id = graphene.ID(
            required=False,
            description="Collection ID or CollectionTranslatableContent ID.",
        )
        external_reference = graphene.String(
            required=False,
            description=f"External ID of a collection to translate.{ADDED_IN_323}",
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = TranslationInput(
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
    def perform_mutation(  # type: ignore[override]
        cls,
        root,
        info: ResolveInfo,
        /,
        *,
        id=None,
        external_reference=None,
        input,
        language_code,
    ):
        response = super().perform_mutation(
            root,
            info,
            id=id,
            external_reference=external_reference,
            input=input,
            language_code=language_code,
        )
        instance = ChannelContext(node=response.collection, channel_slug=None)
        return cls(**{cls._meta.return_field_name: instance})

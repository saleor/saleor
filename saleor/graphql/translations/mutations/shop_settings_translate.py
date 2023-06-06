import graphene

from ....core.tracing import traced_atomic_transaction
from ....permission.enums import SitePermissions
from ....site.models import SiteSettings
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_SHOP
from ...core.enums import LanguageCodeEnum
from ...core.mutations import BaseMutation
from ...core.types import TranslationError
from ...plugins.dataloaders import get_plugin_manager_promise
from ...shop.types import Shop
from ...site.dataloaders import get_site_promise
from .utils import validate_input_against_model


class ShopSettingsTranslationInput(graphene.InputObjectType):
    header_text = graphene.String()
    description = graphene.String()


class ShopSettingsTranslate(BaseMutation):
    shop = graphene.Field(Shop, description="Updated shop settings.")

    class Arguments:
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = ShopSettingsTranslationInput(
            description="Fields required to update shop settings translations.",
            required=True,
        )

    class Meta:
        description = "Creates/updates translations for shop settings."
        doc_category = DOC_CATEGORY_SHOP
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, input, language_code
    ):
        site = get_site_promise(info.context).get()
        instance = site.settings
        validate_input_against_model(SiteSettings, input)
        manager = get_plugin_manager_promise(info.context).get()
        with traced_atomic_transaction():
            translation, created = instance.translations.update_or_create(
                language_code=language_code, defaults=input
            )

        if created:
            cls.call_event(manager.translation_created, translation)
        else:
            cls.call_event(manager.translation_updated, translation)

        return ShopSettingsTranslate(shop=Shop())

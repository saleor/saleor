import graphene

from ....core.tracing import traced_atomic_transaction
from ....permission.enums import SitePermissions
from ....product import models as product_models
from ...channel import ChannelContext
from ...core import ResolveInfo
from ...core.enums import LanguageCodeEnum
from ...core.types import TranslationError
from ...plugins.dataloaders import get_plugin_manager_promise
from ...product.types import Product
from .utils import BaseTranslateMutation, TranslationInput


class ProductTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(
            required=True,
            description="Product ID or ProductTranslatableContent ID.",
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = TranslationInput(
            required=True, description="Fields required to update product translations."
        )

    class Meta:
        description = "Creates/updates translations for a product."
        model = product_models.Product
        object_type = Product
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, input, language_code
    ):
        node_id = cls.clean_node_id(id)[0]
        instance = cls.get_node_or_error(info, node_id, only_type=Product)
        cls.validate_input(input)
        manager = get_plugin_manager_promise(info.context).get()
        with traced_atomic_transaction():
            translation, created = instance.translations.update_or_create(
                language_code=language_code, defaults=input
            )
            product = ChannelContext(node=instance, channel_slug=None)
            if created:
                cls.call_event(manager.translation_created, translation)
            else:
                cls.call_event(manager.translation_updated, translation)

        return cls(**{cls._meta.return_field_name: product})

import graphene

from ....core.tracing import traced_atomic_transaction
from ....permission.enums import SitePermissions
from ....product import models as product_models
from ...core import ResolveInfo
from ...core.context import ChannelContext
from ...core.descriptions import ADDED_IN_323
from ...core.enums import LanguageCodeEnum
from ...core.types import TranslationError
from ...plugins.dataloaders import get_plugin_manager_promise
from ...product.types import ProductVariant
from .utils import BaseTranslateMutation, NameTranslationInput


class ProductVariantTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(
            required=False,
            description="ProductVariant ID or ProductVariantTranslatableContent ID.",
        )
        external_reference = graphene.String(
            required=False,
            description=f"External ID of a product variant to translate.{ADDED_IN_323}",
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = NameTranslationInput(
            required=True,
            description="Fields required to update product variant translations.",
        )

    class Meta:
        description = "Creates/updates translations for a product variant."
        model = product_models.ProductVariant
        object_type = ProductVariant
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        id=None,
        external_reference=None,
        input,
        language_code,
    ):
        node_id = cls.clean_node_id_or_external_reference(id, external_reference)[0]
        variant_pk = cls.get_global_id_or_error(node_id, only_type=ProductVariant)
        variant = product_models.ProductVariant.objects.get(pk=variant_pk)
        cls.validate_input(input)
        manager = get_plugin_manager_promise(info.context).get()
        with traced_atomic_transaction():
            translation, created = variant.translations.update_or_create(
                language_code=language_code, defaults=input
            )
            context = ChannelContext(node=variant, channel_slug=None)
        cls.call_event(manager.product_variant_updated, context.node)

        if created:
            cls.call_event(manager.translations_created, [translation])
        else:
            cls.call_event(manager.translations_updated, [translation])

        return cls(**{cls._meta.return_field_name: context})

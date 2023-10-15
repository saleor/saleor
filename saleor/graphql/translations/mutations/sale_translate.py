import graphene
from django.core.exceptions import ValidationError

from ....discount import models as discount_models
from ....discount.error_codes import DiscountErrorCode
from ....permission.enums import SitePermissions
from ...channel import ChannelContext
from ...core import ResolveInfo
from ...core.descriptions import DEPRECATED_IN_3X_MUTATION
from ...core.enums import LanguageCodeEnum
from ...core.types import TranslationError
from ...core.utils import from_global_id_or_error, raise_validation_error
from ...discount.types import Sale
from ...plugins.dataloaders import get_plugin_manager_promise
from .utils import BaseTranslateMutation, NameTranslationInput


class SaleTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description="Sale ID or SaleTranslatableContent ID."
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = NameTranslationInput(
            required=True, description="Fields required to update sale translations."
        )

    class Meta:
        description = (
            "Creates/updates translations for a sale."
            + DEPRECATED_IN_3X_MUTATION
            + " Use `PromotionTranslate` mutation instead."
        )
        model = discount_models.Promotion
        object_type = Sale
        return_field_name = "sale"
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, root, info: ResolveInfo, /, *, id, input, language_code
    ):
        instance = cls.get_promotion_instance(id)
        cls.validate_input(input)

        input = cls.pre_update_or_create(instance, input)

        translation, created = instance.translations.update_or_create(
            language_code=language_code, defaults=input
        )
        manager = get_plugin_manager_promise(info.context).get()

        if created:
            cls.call_event(manager.translation_created, translation)
        else:
            cls.call_event(manager.translation_updated, translation)

        return cls(
            **{
                cls._meta.return_field_name: ChannelContext(
                    node=instance, channel_slug=None
                )
            }
        )

    @classmethod
    def get_promotion_instance(cls, id):
        if not id:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "This field is required", code=DiscountErrorCode.REQUIRED.value
                    )
                }
            )
        type, node_pk = from_global_id_or_error(id, raise_error=False)
        if type in ("Promotion", "PromotionTranslatableContent"):
            raise_validation_error(
                field="id",
                message="Provided ID refers to Promotion model. "
                "Please use 'promotionTranslate' mutation instead.",
                code=DiscountErrorCode.INVALID.value,
            )
        elif type == "SaleTranslatableContent":
            id = graphene.Node.to_global_id("Sale", node_pk)

        object_id = cls.get_global_id_or_error(id, "Sale")
        try:
            return discount_models.Promotion.objects.get(old_sale_id=object_id)
        except discount_models.Promotion.DoesNotExist:
            raise_validation_error(
                field="id",
                message="Sale with given ID can't be found.",
                code=DiscountErrorCode.NOT_FOUND,
            )

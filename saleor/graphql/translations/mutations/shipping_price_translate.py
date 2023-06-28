import graphene

from ....permission.enums import SitePermissions
from ....shipping import models as shipping_models
from ...channel import ChannelContext
from ...core import ResolveInfo
from ...core.descriptions import RICH_CONTENT
from ...core.enums import LanguageCodeEnum
from ...core.fields import JSONString
from ...core.types import TranslationError
from ...shipping.types import ShippingMethodType
from .utils import BaseTranslateMutation, NameTranslationInput


class ShippingPriceTranslationInput(NameTranslationInput):
    description = JSONString(
        description="Translated shipping method description." + RICH_CONTENT
    )


class ShippingPriceTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(
            required=True,
            description=(
                "ShippingMethodType ID or ShippingMethodTranslatableContent ID."
            ),
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = ShippingPriceTranslationInput(
            required=True,
            description="Fields required to update shipping price translations.",
        )

    class Meta:
        description = "Creates/updates translations for a shipping method."
        model = shipping_models.ShippingMethod
        object_type = ShippingMethodType
        error_type_class = TranslationError
        error_type_field = "translation_errors"
        permissions = (SitePermissions.MANAGE_TRANSLATIONS,)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, root, info: ResolveInfo, /, *, id, input, language_code
    ):
        response = super().perform_mutation(
            root, info, id=id, input=input, language_code=language_code
        )
        instance = ChannelContext(node=response.shippingMethod, channel_slug=None)
        return cls(**{cls._meta.return_field_name: instance})

    @classmethod
    def get_node_or_error(  # type: ignore[override]
        cls,
        info: ResolveInfo,
        node_id,
        *,
        field="id",
        only_type=None,
        code="not_found",
    ):
        if only_type is ShippingMethodType:
            only_type = None
        return super().get_node_or_error(
            info,
            node_id,
            field=field,
            only_type=only_type,
            qs=shipping_models.ShippingMethod.objects,
            code=code,
        )

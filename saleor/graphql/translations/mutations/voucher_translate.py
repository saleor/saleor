import graphene

from ....discount import models as discount_models
from ....permission.enums import SitePermissions
from ...channel import ChannelContext
from ...core import ResolveInfo
from ...core.enums import LanguageCodeEnum
from ...core.types import TranslationError
from ...discount.types import Voucher
from .utils import BaseTranslateMutation, NameTranslationInput


class VoucherTranslate(BaseTranslateMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description="Voucher ID or VoucherTranslatableContent ID."
        )
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="Translation language code."
        )
        input = NameTranslationInput(
            required=True, description="Fields required to update voucher translations."
        )

    class Meta:
        description = "Creates/updates translations for a voucher."
        model = discount_models.Voucher
        object_type = Voucher
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
        instance = ChannelContext(node=response.voucher, channel_slug=None)
        return cls(**{cls._meta.return_field_name: instance})

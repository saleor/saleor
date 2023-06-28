import graphene
from django.core.exceptions import ValidationError

from ....permission.enums import GiftcardPermissions
from ....site import GiftCardSettingsExpiryType
from ....site.error_codes import GiftCardSettingsErrorCode
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_GIFT_CARDS
from ...core.mutations import BaseMutation
from ...core.types import (
    BaseInputObjectType,
    GiftCardSettingsError,
    TimePeriodInputType,
)
from ...site.dataloaders import get_site_promise
from ..enums import GiftCardSettingsExpiryTypeEnum
from ..types import GiftCardSettings


class GiftCardSettingsUpdateInput(BaseInputObjectType):
    expiry_type = GiftCardSettingsExpiryTypeEnum(
        description="Defines gift card default expiry settings."
    )
    expiry_period = TimePeriodInputType(description="Defines gift card expiry period.")

    class Meta:
        doc_category = DOC_CATEGORY_GIFT_CARDS


class GiftCardSettingsUpdate(BaseMutation):
    gift_card_settings = graphene.Field(
        GiftCardSettings, description="Gift card settings."
    )

    class Arguments:
        input = GiftCardSettingsUpdateInput(
            required=True, description="Fields required to update gift card settings."
        )

    class Meta:
        description = "Update gift card settings."
        doc_category = DOC_CATEGORY_GIFT_CARDS
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardSettingsError

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        site = get_site_promise(info.context).get()
        instance = site.settings
        input = data["input"]
        cls.clean_input(input, instance)

        expiry_period = input.get("expiry_period")
        instance.gift_card_expiry_period_type = (
            expiry_period["type"] if expiry_period else None
        )
        instance.gift_card_expiry_period = (
            expiry_period["amount"] if expiry_period else None
        )
        update_fields = ["gift_card_expiry_period", "gift_card_expiry_period_type"]

        if expiry_type := input.get("expiry_type"):
            instance.gift_card_expiry_type = expiry_type
            update_fields.append("gift_card_expiry_type")

        instance.save(update_fields=update_fields)
        return GiftCardSettingsUpdate(gift_card_settings=instance)

    @staticmethod
    def clean_input(input, instance):
        expiry_type = input.get("expiry_type") or instance.gift_card_expiry_type
        if (
            expiry_type == GiftCardSettingsExpiryType.EXPIRY_PERIOD
            and input.get("expiry_period") is None
        ):
            raise ValidationError(
                {
                    "expiry_period": ValidationError(
                        "Expiry period settings are required for expiry period "
                        "gift card settings.",
                        code=GiftCardSettingsErrorCode.REQUIRED.value,
                    )
                }
            )
        elif expiry_type == GiftCardSettingsExpiryType.NEVER_EXPIRE:
            input["expiry_period"] = None

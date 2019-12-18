import graphene
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from ...account.models import User
from ...core.permissions import GiftcardPermissions
from ...core.utils.promo_code import (
    PromoCodeAlreadyExists,
    generate_promo_code,
    is_available_promo_code,
)
from ...giftcard import models
from ...giftcard.error_codes import GiftCardErrorCode
from ...giftcard.utils import activate_gift_card, deactivate_gift_card
from ..core.mutations import BaseMutation, ModelMutation
from ..core.scalars import Decimal
from ..core.types.common import GiftCardError
from .types import GiftCard


class GiftCardUpdateInput(graphene.InputObjectType):
    start_date = graphene.types.datetime.Date(
        description="Start date of the gift card in ISO 8601 format."
    )
    end_date = graphene.types.datetime.Date(
        description="End date of the gift card in ISO 8601 format."
    )
    balance = Decimal(description="Value of the gift card.")
    user_email = graphene.String(
        required=False, description="The customer's email of the gift card buyer."
    )


class GiftCardCreateInput(GiftCardUpdateInput):
    code = graphene.String(required=False, description="Code to use the gift card.")


class GiftCardCreate(ModelMutation):
    class Arguments:
        input = GiftCardCreateInput(
            required=True, description="Fields required to create a gift card."
        )

    class Meta:
        description = "Creates a new gift card."
        model = models.GiftCard
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError
        error_type_field = "gift_card_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        code = data.get("code", None)
        if not code and not instance.pk:
            data["code"] = generate_promo_code()
        elif not is_available_promo_code(code):
            raise PromoCodeAlreadyExists(code=GiftCardErrorCode.ALREADY_EXISTS)
        cleaned_input = super().clean_input(info, instance, data)
        balance = cleaned_input.get("balance", None)
        if balance:
            cleaned_input["current_balance_amount"] = balance
            cleaned_input["initial_balance_amount"] = balance
        user_email = data.get("user_email", None)
        if user_email:
            try:
                cleaned_input["user"] = User.objects.get(email=user_email)
            except ObjectDoesNotExist:
                raise ValidationError(
                    {
                        "email": ValidationError(
                            "Customer with this email doesn't exist.",
                            code=GiftCardErrorCode.NOT_FOUND,
                        )
                    }
                )
        return cleaned_input


class GiftCardUpdate(GiftCardCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a gift card to update.")
        input = GiftCardUpdateInput(
            required=True, description="Fields required to update a gift card."
        )

    class Meta:
        description = "Update a gift card."
        model = models.GiftCard
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError
        error_type_field = "gift_card_errors"


class GiftCardDeactivate(BaseMutation):
    gift_card = graphene.Field(GiftCard, description="A gift card to deactivate.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of a gift card to deactivate.")

    class Meta:
        description = "Deactivate a gift card."
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError
        error_type_field = "gift_card_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        gift_card_id = data.get("id")
        gift_card = cls.get_node_or_error(
            info, gift_card_id, field="gift_card_id", only_type=GiftCard
        )
        deactivate_gift_card(gift_card)
        return GiftCardDeactivate(gift_card=gift_card)


class GiftCardActivate(BaseMutation):
    gift_card = graphene.Field(GiftCard, description="A gift card to activate.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of a gift card to activate.")

    class Meta:
        description = "Activate a gift card."
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError
        error_type_field = "gift_card_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        gift_card_id = data.get("id")
        gift_card = cls.get_node_or_error(
            info, gift_card_id, field="gift_card_id", only_type=GiftCard
        )
        activate_gift_card(gift_card)
        return GiftCardActivate(gift_card=gift_card)

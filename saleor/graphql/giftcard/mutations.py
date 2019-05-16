from datetime import date

import graphene
from django.core.exceptions import ValidationError

from ...giftcard import models
from ...giftcard.utils import generate_gift_card_code
from ..core.mutations import BaseMutation, ModelMutation
from ..core.scalars import Decimal
from .types import GiftCard


class GiftCardInput(graphene.InputObjectType):
    code = graphene.String(decription="Code to use the gift card.")
    start_date = graphene.types.datetime.Date(
        description="Start date of the gift card in ISO 8601 format."
    )
    expiration_date = graphene.types.datetime.Date(
        description="End date of the gift card in ISO 8601 format."
    )
    balance = Decimal(description="Value of the gift card.")


class GiftCardCreate(ModelMutation):
    class Arguments:
        input = GiftCardInput(
            required=True, description="Fields required to create a gift card."
        )

    class Meta:
        description = "Creates a new gift card"
        model = models.GiftCard
        permissions = ("giftcard.manage_gift_card",)

    @classmethod
    def clean_input(cls, info, instance, data):
        code = data.get("code", None)
        if code == "":
            data["code"] = generate_gift_card_code()
        cleaned_input = super().clean_input(info, instance, data)
        balance = cleaned_input.get("balance", None)
        if balance:
            cleaned_input["current_balance"] = balance
            cleaned_input["initial_balance"] = balance
        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.creator = info.context.user
        super().save(info, instance, cleaned_input)


class GiftCardUpdate(GiftCardCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a gift card to update.")
        input = GiftCardInput(
            required=True, description="Fields required to update a gift card."
        )

    class Meta:
        description = "Update a gift card."
        model = models.GiftCard
        permissions = ("giftcard.manage_gift_card",)

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.last_used_on = date.today()
        super().save(info, instance, cleaned_input)


class GiftCardDeactivate(BaseMutation):
    gift_card = graphene.Field(GiftCard, description="A gift card to deactivate.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of a gift card to deactivate.")

    class Meta:
        description = "Deactivate a gift card."
        permissions = ("giftcard.manage_gift_card",)

    @classmethod
    def perform_mutation(cls, _root, info, id):
        gift_card = cls.get_node_or_error(
            info, id, field="gift_card_id", only_type=GiftCard
        )
        gift_card.is_active = False
        gift_card.last_used_on = date.today()
        gift_card.save()
        return GiftCardDeactivate(gift_card=gift_card)


class GiftCardVerify(BaseMutation):
    gift_card = graphene.Field(GiftCard, description="A gift card to verify.")

    class Arguments:
        code = graphene.String(required=True, description="Code of a gift card.")

    class Meta:
        description = "Verify a gift card."

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        code = data.get("code")
        try:
            gift_card = models.GiftCard.objects.get(code=code)
        except models.GiftCard.DoesNotExist:
            gift_card = None
            raise ValidationError({"code": "Incorrect gift card code."})
        if gift_card:
            if not gift_card.is_active:
                raise ValidationError({"is_active": "Gift card is inactive."})
            if gift_card.expiration_date and date.today() > gift_card.expiration_date:
                raise ValidationError({"expiration_date": "Gift card expired."})
        return GiftCardDeactivate(gift_card=gift_card)

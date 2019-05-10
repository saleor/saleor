import graphene

from ...giftcard import models
from ...giftcard.utils import generate_gift_card_code
from ..core.mutations import ModelMutation
from ..core.scalars import Decimal
from .types import GiftCard


class GiftCardInput(graphene.InputObjectType):
    code = graphene.String(decription='Code to use the gift card.')
    start_date = graphene.types.datetime.Date(
        description='Start date of the gift card in ISO 8601 format.')
    expiration_date = graphene.types.datetime.Date(
        description='End date of the gift card in ISO 8601 format.')
    initial_balance = Decimal(description='Value of the gift card.')


class GiftCardCreate(ModelMutation):
    class Arguments:
        input = GiftCardInput(
            required=True,
            description='Fields required to create a gift card.')

    class Meta:
        description = 'Creates a new gift card'
        model = models.GiftCard
        permissions = ('giftcard.manage_gift_card', )

    @classmethod
    def clean_input(cls, info, instance, data):
        code = data.get('code', None)
        if code == '':
            data['code'] = generate_gift_card_code()
        cleaned_input = super().clean_input(info, instance, data)
        initial_balance = cleaned_input.get('initial_balance', None)
        if initial_balance:
            cleaned_input['current_balance'] = initial_balance
        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.creator = info.context.user
        super().save(info, instance, cleaned_input)

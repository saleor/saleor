import graphene
from django.core.exceptions import ValidationError

from ...core.permissions import GiftcardPermissions
from ...core.utils.promo_code import generate_promo_code
from ...core.utils.validators import date_passed, user_is_valid
from ...giftcard import GiftCardExpiryType, events, models
from ...giftcard.error_codes import GiftCardErrorCode
from ...giftcard.utils import activate_gift_card, deactivate_gift_card
from ..core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ..core.types.common import GiftCardError, PriceInput, TimePeriodInputType
from ..core.validators import validate_price_precision
from .enums import GiftCardExpiryTypeEnum
from .types import GiftCard


class GiftCardExpirySettingsInput(graphene.InputObjectType):
    expiry_type = GiftCardExpiryTypeEnum(
        description="The gift card expiry type.", required=True
    )
    expiry_date = graphene.types.datetime.Date(description="The gift card expiry date.")
    expiry_period = TimePeriodInputType(description="The gift card expiry period.")


class GiftCardInput(graphene.InputObjectType):
    tag = graphene.String(description="The gift card tag.")

    # DEPRECATED
    start_date = graphene.types.datetime.Date(
        description=(
            "Start date of the gift card in ISO 8601 format. "
            "DEPRECATED: Will be removed in Saleor 4.0."
        )
    )
    end_date = graphene.types.datetime.Date(
        description=(
            "End date of the gift card in ISO 8601 format."
            "DEPRECATED: Will be removed in Saleor 4.0. "
            "Use expiryDate from expirySettings instead."
        )
    )


class GiftCardCreateInput(GiftCardInput):
    balance = graphene.Field(
        PriceInput, description="Balance of the gift card.", required=True
    )
    user_email = graphene.String(
        required=False,
        description="Email of the customer to whom gift card will be sent.",
    )
    expiry_settings = GiftCardExpirySettingsInput(
        description="The gift card expiry settings.", required=True
    )
    code = graphene.String(
        required=False,
        description=(
            "Code to use the gift card. "
            "DEPRECATED: The code is auto generated. "
            "The field will be removed in Saleor 4.0"
        ),
    )
    note = graphene.String(description="The gift card note from the staff member.")


class GiftCardUpdateInput(GiftCardInput):
    balance = graphene.Field(
        PriceInput, description="Balance of the gift card.", required=False
    )
    expiry_settings = GiftCardExpirySettingsInput(
        description="The gift card expiry settings.", required=False
    )


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
        if instance.pk is None:
            data["code"] = generate_promo_code()

        cleaned_input = super().clean_input(info, instance, data)
        cls.clean_expiry_settings(cleaned_input)
        cls.clean_balance(cleaned_input, instance.currency)

        # TODO: send an email to the customer from user_email field in SALEOR-3901
        data.get("user_email", None)

        user = info.context.user
        if user_is_valid(user):
            cleaned_input["created_by"] = user
            cleaned_input["created_by_email"] = user.email
        cleaned_input["app"] = info.context.app
        return cleaned_input

    @staticmethod
    def clean_expiry_settings(cleaned_input):
        expiry_settings = cleaned_input.pop("expiry_settings", None)
        if not expiry_settings:
            return
        type = expiry_settings["expiry_type"]
        cleaned_input["expiry_type"] = type
        if type == GiftCardExpiryType.EXPIRY_DATE:
            expiry_date = expiry_settings.get("expiry_date")
            if not expiry_date:
                raise ValidationError(
                    {
                        "expiry_date": ValidationError(
                            "Expiry date is required for chosen expiry type.",
                            code=GiftCardErrorCode.REQUIRED,
                        )
                    }
                )
            if date_passed(expiry_date):
                raise ValidationError(
                    {
                        "expiry_date": ValidationError(
                            "Expiry date cannot be in the past.",
                            code=GiftCardErrorCode.INVALID,
                        )
                    }
                )
            cleaned_input["expiry_date"] = expiry_date
        elif type == GiftCardExpiryType.EXPIRY_PERIOD:
            expiry_period = expiry_settings.get("expiry_period")
            if not expiry_period:
                raise ValidationError(
                    {
                        "expiry_period": ValidationError(
                            "Expiry period settings are required for chosen "
                            "expiry type.",
                            code=GiftCardErrorCode.REQUIRED,
                        )
                    }
                )
            cleaned_input["expiry_period"] = expiry_period["amount"]
            cleaned_input["expiry_period_type"] = expiry_period["type"]

    @staticmethod
    def clean_balance(cleaned_input, currency):
        balance = cleaned_input.pop("balance", None)
        if balance:
            amount = balance["amount"]
            currency = balance["currency"]
            try:
                validate_price_precision(amount, currency)
            except ValidationError as error:
                error.code = GiftCardErrorCode.INVALID.value
                raise ValidationError({"balance": error})
            cleaned_input["currency"] = currency
            cleaned_input["current_balance_amount"] = amount
            cleaned_input["initial_balance_amount"] = amount

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        events.gift_card_issued_event(
            gift_card=instance,
            user=info.context.user,
            app=info.context.app,
        )


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


class GiftCardDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(description="ID of the gift card to delete.", required=True)

    class Meta:
        description = "Delete gift card."
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

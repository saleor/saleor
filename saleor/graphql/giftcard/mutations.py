from copy import deepcopy
from typing import Iterable

import graphene
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from ...account.models import User
from ...core.permissions import GiftcardPermissions
from ...core.tracing import traced_atomic_transaction
from ...core.utils.promo_code import generate_promo_code
from ...core.utils.validators import is_date_in_future, user_is_valid
from ...giftcard import events, models
from ...giftcard.error_codes import GiftCardErrorCode
from ...giftcard.notifications import send_gift_card_notification
from ...giftcard.utils import (
    activate_gift_card,
    deactivate_gift_card,
    is_gift_card_expired,
)
from ..app.dataloaders import load_app
from ..core.descriptions import ADDED_IN_31, DEPRECATED_IN_3X_INPUT, PREVIEW_FEATURE
from ..core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ..core.scalars import PositiveDecimal
from ..core.types import GiftCardError, NonNullList, PriceInput
from ..core.utils import validate_required_string_field
from ..core.validators import validate_price_precision
from ..utils.validators import check_for_duplicates
from .types import GiftCard, GiftCardEvent


def clean_gift_card(gift_card: GiftCard):
    if is_gift_card_expired(gift_card):
        raise ValidationError(
            {
                "id": ValidationError(
                    "Expired gift card cannot be activated and resend.",
                    code=GiftCardErrorCode.EXPIRED_GIFT_CARD.value,
                )
            }
        )


class GiftCardInput(graphene.InputObjectType):
    add_tags = NonNullList(
        graphene.String,
        description="The gift card tags to add." + ADDED_IN_31 + PREVIEW_FEATURE,
    )
    expiry_date = graphene.types.datetime.Date(
        description="The gift card expiry date." + ADDED_IN_31 + PREVIEW_FEATURE
    )

    # DEPRECATED
    start_date = graphene.types.datetime.Date(
        description=(
            f"Start date of the gift card in ISO 8601 format. {DEPRECATED_IN_3X_INPUT}"
        )
    )
    end_date = graphene.types.datetime.Date(
        description=(
            "End date of the gift card in ISO 8601 format. "
            f"{DEPRECATED_IN_3X_INPUT} Use `expiryDate` from `expirySettings` instead."
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
    channel = graphene.String(
        description=(
            "Slug of a channel from which the email should be sent."
            + ADDED_IN_31
            + PREVIEW_FEATURE
        )
    )
    is_active = graphene.Boolean(
        required=True,
        description=(
            "Determine if gift card is active." + ADDED_IN_31 + PREVIEW_FEATURE
        ),
    )
    code = graphene.String(
        required=False,
        description=(
            "Code to use the gift card. "
            f"{DEPRECATED_IN_3X_INPUT} The code is now auto generated."
        ),
    )
    note = graphene.String(
        description=(
            "The gift card note from the staff member." + ADDED_IN_31 + PREVIEW_FEATURE
        )
    )


class GiftCardUpdateInput(GiftCardInput):
    remove_tags = NonNullList(
        graphene.String,
        description="The gift card tags to remove." + ADDED_IN_31 + PREVIEW_FEATURE,
    )
    balance_amount = PositiveDecimal(
        description="The gift card balance amount." + ADDED_IN_31 + PREVIEW_FEATURE,
        required=False,
    )


class GiftCardCreate(ModelMutation):
    class Arguments:
        input = GiftCardCreateInput(
            required=True, description="Fields required to create a gift card."
        )

    class Meta:
        description = "Creates a new gift card."
        model = models.GiftCard
        object_type = GiftCard
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError
        error_type_field = "gift_card_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)

        # perform only when gift card is created
        if instance.pk is None:
            cleaned_input["code"] = generate_promo_code()
            cls.set_created_by_user(cleaned_input, info)

        cls.clean_expiry_date(cleaned_input, instance)
        cls.clean_balance(cleaned_input, instance)

        if email := data.get("user_email"):
            try:
                validate_email(email)
            except ValidationError:
                raise ValidationError(
                    {
                        "email": ValidationError(
                            "Provided email is invalid.",
                            code=GiftCardErrorCode.INVALID.value,
                        )
                    }
                )
            if not data.get("channel"):
                raise ValidationError(
                    {
                        "channel": ValidationError(
                            "Channel slug must be specified "
                            "when user_email is provided.",
                            code=GiftCardErrorCode.REQUIRED.value,
                        )
                    }
                )
            cleaned_input["customer_user"] = User.objects.filter(email=email).first()

        return cleaned_input

    @staticmethod
    def set_created_by_user(cleaned_input, info):
        user = info.context.user
        if user_is_valid(user):
            cleaned_input["created_by"] = user
            cleaned_input["created_by_email"] = user.email
        cleaned_input["app"] = load_app(info.context)

    @classmethod
    def clean_expiry_date(cls, cleaned_input, instance):
        expiry_date = cleaned_input.get("expiry_date")
        if expiry_date and not is_date_in_future(expiry_date):
            raise ValidationError(
                {
                    "expiry_date": ValidationError(
                        "Expiry date must be in the future.",
                        code=GiftCardErrorCode.INVALID.value,
                    )
                }
            )

    @staticmethod
    def clean_balance(cleaned_input, instance):
        balance = cleaned_input.pop("balance", None)
        if balance:
            amount = balance["amount"]
            currency = balance["currency"]
            try:
                validate_price_precision(amount, currency)
            except ValidationError as error:
                error.code = GiftCardErrorCode.INVALID.value
                raise ValidationError({"balance": error})
            if instance.pk:
                if currency != instance.currency:
                    raise ValidationError(
                        {
                            "balance": ValidationError(
                                "Cannot change gift card currency.",
                                code=GiftCardErrorCode.INVALID.value,
                            )
                        }
                    )
            if not amount > 0:
                raise ValidationError(
                    {
                        "balance": ValidationError(
                            "Balance amount have to be greater than 0.",
                            code=GiftCardErrorCode.INVALID.value,
                        )
                    }
                )
            cleaned_input["currency"] = currency
            cleaned_input["current_balance_amount"] = amount
            cleaned_input["initial_balance_amount"] = amount

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        user = info.context.user
        app = load_app(info.context)
        events.gift_card_issued_event(
            gift_card=instance,
            user=user,
            app=app,
        )
        if note := cleaned_input.get("note"):
            events.gift_card_note_added_event(
                gift_card=instance, user=user, app=app, message=note
            )
        if email := cleaned_input.get("user_email"):
            send_gift_card_notification(
                cleaned_input.get("created_by"),
                cleaned_input.get("app"),
                cleaned_input["customer_user"],
                email,
                instance,
                info.context.plugins,
                channel_slug=cleaned_input["channel"],
                resending=False,
            )
        info.context.plugins.gift_card_created(instance)

    @staticmethod
    def assign_gift_card_tags(instance: models.GiftCard, tags_values: Iterable[str]):
        add_tags = {tag.lower() for tag in tags_values}
        add_tags_instances = models.GiftCardTag.objects.filter(name__in=add_tags)
        tags_to_create = add_tags - set(
            add_tags_instances.values_list("name", flat=True)
        )
        models.GiftCardTag.objects.bulk_create(
            [models.GiftCardTag(name=tag) for tag in tags_to_create]
        )
        instance.tags.add(*add_tags_instances)

    @classmethod
    @traced_atomic_transaction()
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        tags = cleaned_data.get("add_tags")
        if tags:
            cls.assign_gift_card_tags(instance, tags)


class GiftCardUpdate(GiftCardCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a gift card to update.")
        input = GiftCardUpdateInput(
            required=True, description="Fields required to update a gift card."
        )

    class Meta:
        description = "Update a gift card."
        model = models.GiftCard
        object_type = GiftCard
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError
        error_type_field = "gift_card_errors"

    @classmethod
    def clean_expiry_date(cls, cleaned_input, instance):
        super().clean_expiry_date(cleaned_input, instance)
        expiry_date = cleaned_input.get("expiry_date")
        if expiry_date and expiry_date == instance.expiry_date:
            del cleaned_input["expiry_date"]

    @staticmethod
    def clean_balance(cleaned_input, instance):
        amount = cleaned_input.pop("balance_amount", None)

        if amount is None:
            return

        currency = instance.currency
        try:
            validate_price_precision(amount, currency)
        except ValidationError as error:
            error.code = GiftCardErrorCode.INVALID.value
            raise ValidationError({"balance_amount": error})
        cleaned_input["current_balance_amount"] = amount
        cleaned_input["initial_balance_amount"] = amount

    @staticmethod
    def clean_tags(cleaned_input):
        error = check_for_duplicates(cleaned_input, "add_tags", "remove_tags", "tags")
        if error:
            error.code = GiftCardErrorCode.DUPLICATED_INPUT_ITEM.value
            raise ValidationError({"tags": error})

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        instance = cls.get_instance(info, **data)

        old_instance = deepcopy(instance)

        data = data.get("input")
        cleaned_input = cls.clean_input(info, instance, data)

        tags_updated = "add_tags" in cleaned_input or "remove_tags" in cleaned_input
        if tags_updated:
            old_tags = list(
                old_instance.tags.order_by("name").values_list("name", flat=True)
            )

        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(info, instance)
        cls.save(info, instance, cleaned_input)
        cls._save_m2m(info, instance, cleaned_input)

        user = info.context.user
        app = load_app(info.context)
        if "initial_balance_amount" in cleaned_input:
            events.gift_card_balance_reset_event(instance, old_instance, user, app)
        if "expiry_date" in cleaned_input:
            events.gift_card_expiry_date_updated_event(
                instance, old_instance, user, app
            )
        if tags_updated:
            events.gift_card_tags_updated_event(instance, old_tags, user, app)

        info.context.plugins.gift_card_updated(instance)
        return cls.success_response(instance)

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        cls.clean_tags(cleaned_input)
        return cleaned_input

    @classmethod
    @traced_atomic_transaction()
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        remove_tags = cleaned_data.get("remove_tags")
        if remove_tags:
            remove_tags = {tag.lower() for tag in remove_tags}
            remove_tags_instances = models.GiftCardTag.objects.filter(
                name__in=remove_tags
            )
            instance.tags.remove(*remove_tags_instances)
            # delete tags without gift card assigned
            remove_tags_instances.filter(gift_cards__isnull=True).delete()


class GiftCardDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(description="ID of the gift card to delete.", required=True)

    class Meta:
        description = "Delete gift card." + ADDED_IN_31 + PREVIEW_FEATURE
        model = models.GiftCard
        object_type = GiftCard
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError
        error_type_field = "gift_card_errors"

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        info.context.plugins.gift_card_deleted(instance)


class GiftCardDeactivate(BaseMutation):
    gift_card = graphene.Field(GiftCard, description="Deactivated gift card.")

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
        # create event only when is_active value has changed
        create_event = gift_card.is_active
        deactivate_gift_card(gift_card)
        if create_event:
            app = load_app(info.context)
            events.gift_card_deactivated_event(
                gift_card=gift_card,
                user=info.context.user,
                app=app,
            )
        info.context.plugins.gift_card_status_changed(gift_card)
        return GiftCardDeactivate(gift_card=gift_card)


class GiftCardActivate(BaseMutation):
    gift_card = graphene.Field(GiftCard, description="Activated gift card.")

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
        clean_gift_card(gift_card)
        # create event only when is_active value has changed
        create_event = not gift_card.is_active
        activate_gift_card(gift_card)
        if create_event:
            app = load_app(info.context)
            events.gift_card_activated_event(
                gift_card=gift_card,
                user=info.context.user,
                app=app,
            )
        info.context.plugins.gift_card_status_changed(gift_card)
        return GiftCardActivate(gift_card=gift_card)


class GiftCardResendInput(graphene.InputObjectType):
    id = graphene.ID(required=True, description="ID of a gift card to resend.")
    email = graphene.String(
        required=False, description="Email to which gift card should be send."
    )
    channel = graphene.String(
        description="Slug of a channel from which the email should be sent.",
        required=True,
    )


class GiftCardResend(BaseMutation):
    gift_card = graphene.Field(GiftCard, description="Gift card which has been sent.")

    class Arguments:
        input = GiftCardResendInput(
            required=True, description="Fields required to resend a gift card."
        )

    class Meta:
        description = "Resend a gift card." + ADDED_IN_31 + PREVIEW_FEATURE
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError

    @classmethod
    def clean_input(cls, data):
        if email := data.get("email"):
            try:
                validate_email(email)
            except ValidationError:
                raise ValidationError(
                    {
                        "email": ValidationError(
                            "Provided email is invalid.",
                            code=GiftCardErrorCode.INVALID.value,
                        )
                    }
                )

        return data

    @classmethod
    def get_target_email(cls, data, gift_card):
        return (
            data.get("email") or gift_card.used_by_email or gift_card.created_by_email
        )

    @classmethod
    def get_customer_user(cls, email):
        return User.objects.filter(email=email).first()

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        data = data.get("input")
        data = cls.clean_input(data)
        gift_card_id = data["id"]
        gift_card = cls.get_node_or_error(
            info, gift_card_id, field="gift_card_id", only_type=GiftCard
        )
        clean_gift_card(gift_card)
        target_email = cls.get_target_email(data, gift_card)
        customer_user = cls.get_customer_user(target_email)
        user = info.context.user
        if not user_is_valid(user):
            user = None
        app = load_app(info.context)
        send_gift_card_notification(
            user,
            app,
            customer_user,
            target_email,
            gift_card,
            info.context.plugins,
            channel_slug=data.get("channel"),
            resending=True,
        )
        return GiftCardResend(gift_card=gift_card)


class GiftCardAddNoteInput(graphene.InputObjectType):
    message = graphene.String(description="Note message.", required=True)


class GiftCardAddNote(BaseMutation):
    gift_card = graphene.Field(GiftCard, description="Gift card with the note added.")
    event = graphene.Field(GiftCardEvent, description="Gift card note created.")

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of the gift card to add a note for."
        )
        input = GiftCardAddNoteInput(
            required=True,
            description="Fields required to create a note for the gift card.",
        )

    class Meta:
        description = "Adds note to the gift card." + ADDED_IN_31 + PREVIEW_FEATURE
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError

    @classmethod
    def clean_input(cls, _info, _instance, data):
        try:
            cleaned_input = validate_required_string_field(data["input"], "message")
        except ValidationError:
            raise ValidationError(
                {
                    "message": ValidationError(
                        "Message can't be empty.",
                        code=GiftCardErrorCode.REQUIRED,
                    )
                }
            )
        return cleaned_input

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        gift_card = cls.get_node_or_error(info, data.get("id"), only_type=GiftCard)
        cleaned_input = cls.clean_input(info, gift_card, data)
        app = load_app(info.context)
        event = events.gift_card_note_added_event(
            gift_card=gift_card,
            user=info.context.user,
            app=app,
            message=cleaned_input["message"],
        )
        info.context.plugins.gift_card_updated(gift_card)
        return GiftCardAddNote(gift_card=gift_card, event=event)

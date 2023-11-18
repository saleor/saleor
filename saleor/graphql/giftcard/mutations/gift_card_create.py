from collections.abc import Iterable

import graphene
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from ....account.models import User
from ....core.tracing import traced_atomic_transaction
from ....core.utils.promo_code import generate_promo_code, is_available_promo_code
from ....core.utils.validators import is_date_in_future
from ....giftcard import events, models
from ....giftcard.error_codes import GiftCardErrorCode
from ....giftcard.notifications import send_gift_card_notification
from ....permission.enums import GiftcardPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_31, DEPRECATED_IN_3X_INPUT
from ...core.doc_category import DOC_CATEGORY_GIFT_CARDS
from ...core.mutations import ModelMutation
from ...core.scalars import Date
from ...core.types import BaseInputObjectType, GiftCardError, NonNullList, PriceInput
from ...core.utils import WebhookEventInfo
from ...core.validators import validate_price_precision
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import GiftCard


class GiftCardInput(BaseInputObjectType):
    add_tags = NonNullList(
        graphene.String,
        description="The gift card tags to add." + ADDED_IN_31,
    )
    expiry_date = Date(description="The gift card expiry date." + ADDED_IN_31)

    # DEPRECATED
    start_date = Date(
        description=(
            f"Start date of the gift card in ISO 8601 format. {DEPRECATED_IN_3X_INPUT}"
        )
    )
    end_date = Date(
        description=(
            "End date of the gift card in ISO 8601 format. "
            f"{DEPRECATED_IN_3X_INPUT} Use `expiryDate` from `expirySettings` instead."
        )
    )

    class Meta:
        doc_category = DOC_CATEGORY_GIFT_CARDS


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
            "Slug of a channel from which the email should be sent." + ADDED_IN_31
        )
    )
    is_active = graphene.Boolean(
        required=True,
        description=("Determine if gift card is active." + ADDED_IN_31),
    )
    code = graphene.String(
        required=False,
        description=(
            "Code to use the gift card. "
            f"{DEPRECATED_IN_3X_INPUT} The code is now auto generated."
        ),
    )
    note = graphene.String(
        description=("The gift card note from the staff member." + ADDED_IN_31)
    )

    class Meta:
        doc_category = DOC_CATEGORY_GIFT_CARDS


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
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.GIFT_CARD_CREATED,
                description="A gift card was created.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.NOTIFY_USER,
                description="A notification for created gift card.",
            ),
        ]

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)

        # perform only when gift card is created
        if instance.pk is None:
            code = cleaned_input.get("code")
            if code and not is_available_promo_code(code):
                raise ValidationError(
                    {
                        "code": ValidationError(
                            "Promo code already exists.",
                            code=GiftCardErrorCode.ALREADY_EXISTS.value,
                        )
                    }
                )

            cleaned_input["code"] = code or generate_promo_code()
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
    def set_created_by_user(cleaned_input, info: ResolveInfo):
        user = info.context.user
        if user:
            cleaned_input["created_by"] = user
            cleaned_input["created_by_email"] = user.email
        cleaned_input["app"] = get_app_promise(info.context).get()

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
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        user = info.context.user
        app = get_app_promise(info.context).get()
        events.gift_card_issued_event(
            gift_card=instance,
            user=user,
            app=app,
        )
        manager = get_plugin_manager_promise(info.context).get()
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
                manager,
                channel_slug=cleaned_input["channel"],
                resending=False,
            )
        cls.call_event(manager.gift_card_created, instance)

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
    def _save_m2m(cls, info: ResolveInfo, instance, cleaned_data):
        with traced_atomic_transaction():
            super()._save_m2m(info, instance, cleaned_data)
            tags = cleaned_data.get("add_tags")
            if tags:
                cls.assign_gift_card_tags(instance, tags)

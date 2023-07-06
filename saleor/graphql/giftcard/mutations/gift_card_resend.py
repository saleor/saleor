import graphene
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from ....account.models import User
from ....giftcard.error_codes import GiftCardErrorCode
from ....giftcard.notifications import send_gift_card_notification
from ....permission.enums import GiftcardPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_31
from ...core.doc_category import DOC_CATEGORY_GIFT_CARDS
from ...core.mutations import BaseMutation
from ...core.types import BaseInputObjectType, GiftCardError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import GiftCard
from .utils import clean_gift_card


class GiftCardResendInput(BaseInputObjectType):
    id = graphene.ID(required=True, description="ID of a gift card to resend.")
    email = graphene.String(
        required=False, description="Email to which gift card should be send."
    )
    channel = graphene.String(
        description="Slug of a channel from which the email should be sent.",
        required=True,
    )

    class Meta:
        doc_category = DOC_CATEGORY_GIFT_CARDS


class GiftCardResend(BaseMutation):
    gift_card = graphene.Field(GiftCard, description="Gift card which has been sent.")

    class Arguments:
        input = GiftCardResendInput(
            required=True, description="Fields required to resend a gift card."
        )

    class Meta:
        description = "Resend a gift card." + ADDED_IN_31
        doc_category = DOC_CATEGORY_GIFT_CARDS
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.NOTIFY_USER,
                description="A notification for gift card resend.",
            )
        ]

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
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
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
        if not user:
            user = None
        app = get_app_promise(info.context).get()
        manager = get_plugin_manager_promise(info.context).get()
        send_gift_card_notification(
            user,
            app,
            customer_user,
            target_email,
            gift_card,
            manager,
            channel_slug=data.get("channel"),
            resending=True,
        )
        return GiftCardResend(gift_card=gift_card)

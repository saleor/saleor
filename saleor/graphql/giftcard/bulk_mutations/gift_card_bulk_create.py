from collections.abc import Iterable

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ....core.tracing import traced_atomic_transaction
from ....core.utils.promo_code import generate_promo_code
from ....core.utils.validators import is_date_in_future
from ....giftcard import events, models
from ....giftcard.error_codes import GiftCardErrorCode
from ....permission.enums import GiftcardPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.utils import get_webhooks_for_event
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_31
from ...core.doc_category import DOC_CATEGORY_GIFT_CARDS
from ...core.mutations import BaseMutation
from ...core.scalars import Date
from ...core.types import BaseInputObjectType, GiftCardError, NonNullList, PriceInput
from ...core.utils import WebhookEventInfo
from ...core.validators import validate_price_precision
from ...plugins.dataloaders import get_plugin_manager_promise
from ..mutations import GiftCardCreate
from ..types import GiftCard


class GiftCardBulkCreateInput(BaseInputObjectType):
    count = graphene.Int(required=True, description="The number of cards to issue.")
    balance = graphene.Field(
        PriceInput, description="Balance of the gift card.", required=True
    )
    tags = NonNullList(
        graphene.String,
        description="The gift card tags.",
    )
    expiry_date = Date(description="The gift card expiry date.")
    is_active = graphene.Boolean(
        required=True, description="Determine if gift card is active."
    )

    class Meta:
        doc_category = DOC_CATEGORY_GIFT_CARDS


class GiftCardBulkCreate(BaseMutation):
    count = graphene.Int(
        required=True,
        default_value=0,
        description="Returns how many objects were created.",
    )
    gift_cards = NonNullList(
        GiftCard,
        required=True,
        default_value=[],
        description="List of created gift cards.",
    )

    class Arguments:
        input = GiftCardBulkCreateInput(
            required=True, description="Fields required to create gift cards."
        )

    class Meta:
        description = "Create gift cards." + ADDED_IN_31
        doc_category = DOC_CATEGORY_GIFT_CARDS
        model = models.GiftCard
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError
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
    @traced_atomic_transaction()
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input
    ):
        cls.clean_count_value(input)
        cls.clean_expiry_date(input)
        cls.clean_balance(input)
        GiftCardCreate.set_created_by_user(input, info)
        tags = input.pop("tags", None)
        instances = cls.create_instances(input, info)
        if tags:
            cls.assign_gift_card_tags(instances, tags)
        transaction.on_commit(
            lambda: cls.call_gift_card_created_on_plugins(instances, info.context)
        )
        return cls(count=len(instances), gift_cards=instances)

    @staticmethod
    def clean_count_value(input_data):
        if not input_data["count"] > 0:
            raise ValidationError(
                {
                    "count": ValidationError(
                        "Count value must be greater than 0.",
                        code=GiftCardErrorCode.INVALID.value,
                    )
                }
            )

    @staticmethod
    def clean_expiry_date(input_data):
        expiry_date = input_data.get("expiry_date")
        if expiry_date and not is_date_in_future(expiry_date):
            raise ValidationError(
                {
                    "expiry_date": ValidationError(
                        "Expiry date cannot be in the past.",
                        code=GiftCardErrorCode.INVALID.value,
                    )
                }
            )

    @staticmethod
    def clean_balance(cleaned_input):
        balance = cleaned_input["balance"]
        amount = balance["amount"]
        currency = balance["currency"]
        try:
            validate_price_precision(amount, currency)
        except ValidationError as error:
            error.code = GiftCardErrorCode.INVALID.value
            raise ValidationError({"balance": error})
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

    @staticmethod
    def create_instances(cleaned_input, info):
        count = cleaned_input.pop("count")
        balance = cleaned_input.pop("balance")
        app = get_app_promise(info.context).get()
        gift_cards = models.GiftCard.objects.bulk_create(
            [
                models.GiftCard(code=generate_promo_code(), **cleaned_input)
                for _ in range(count)
            ]
        )
        events.gift_cards_issued_event(gift_cards, info.context.user, app, balance)
        return gift_cards

    @staticmethod
    def assign_gift_card_tags(
        instances: Iterable[models.GiftCard], tags_values: Iterable[str]
    ):
        tags = {tag.lower() for tag in tags_values}
        tags_instances = models.GiftCardTag.objects.filter(name__in=tags)
        tags_to_create = tags - set(tags_instances.values_list("name", flat=True))
        models.GiftCardTag.objects.bulk_create(
            [models.GiftCardTag(name=tag) for tag in tags_to_create]
        )
        for tag_instance in tags_instances.iterator():
            tag_instance.gift_cards.set(instances)

    @classmethod
    def call_gift_card_created_on_plugins(cls, instances, context):
        webhooks = get_webhooks_for_event(WebhookEventAsyncType.GIFT_CARD_CREATED)
        manager = get_plugin_manager_promise(context).get()
        for instance in instances:
            cls.call_event(manager.gift_card_created, instance, webhooks=webhooks)

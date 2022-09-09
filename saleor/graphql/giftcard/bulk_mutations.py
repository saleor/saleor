from typing import Iterable

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ...core.permissions import GiftcardPermissions
from ...core.tracing import traced_atomic_transaction
from ...core.utils.promo_code import generate_promo_code
from ...core.utils.validators import is_date_in_future
from ...giftcard import events, models
from ...giftcard.error_codes import GiftCardErrorCode
from ...giftcard.utils import is_gift_card_expired
from ..app.dataloaders import load_app
from ..core.descriptions import ADDED_IN_31, PREVIEW_FEATURE
from ..core.mutations import BaseBulkMutation, BaseMutation, ModelBulkDeleteMutation
from ..core.types import GiftCardError, NonNullList, PriceInput
from ..core.validators import validate_price_precision
from ..plugins.dataloaders import load_plugin_manager
from .mutations import GiftCardCreate
from .types import GiftCard


class GiftCardBulkCreateInput(graphene.InputObjectType):
    count = graphene.Int(required=True, description="The number of cards to issue.")
    balance = graphene.Field(
        PriceInput, description="Balance of the gift card.", required=True
    )
    tags = NonNullList(
        graphene.String,
        description="The gift card tags.",
    )
    expiry_date = graphene.types.datetime.Date(description="The gift card expiry date.")
    is_active = graphene.Boolean(
        required=True, description="Determine if gift card is active."
    )


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
        description = "Create gift cards." + ADDED_IN_31 + PREVIEW_FEATURE
        model = models.GiftCard
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        input_data = data["input"]
        cls.clean_count_value(input_data)
        cls.clean_expiry_date(input_data)
        cls.clean_balance(input_data)
        GiftCardCreate.set_created_by_user(input_data, info)
        tags = input_data.pop("tags", None)
        instances = cls.create_instances(input_data, info)
        if tags:
            cls.assign_gift_card_tags(instances, tags)
        manager = load_plugin_manager(info.context)
        transaction.on_commit(
            lambda: cls.call_gift_card_created_on_plugins(instances, manager)
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
        app = load_app(info.context)
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

    @staticmethod
    def call_gift_card_created_on_plugins(instances, manager):
        for instance in instances:
            manager.gift_card_created(instance)


class GiftCardBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of gift card IDs to delete."
        )

    class Meta:
        description = "Delete gift cards." + ADDED_IN_31 + PREVIEW_FEATURE
        model = models.GiftCard
        object_type = GiftCard
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError

    @classmethod
    def bulk_action(cls, info, queryset):
        instances = [card for card in queryset]
        queryset.delete()
        manager = load_plugin_manager(info.context)
        for instance in instances:
            manager.gift_card_deleted(instance)


class GiftCardBulkActivate(BaseBulkMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of gift card IDs to activate."
        )

    class Meta:
        description = "Activate gift cards." + ADDED_IN_31 + PREVIEW_FEATURE
        model = models.GiftCard
        object_type = GiftCard
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError

    @classmethod
    def clean_instance(cls, info, instance):
        if is_gift_card_expired(instance):
            raise ValidationError(
                "Cannot activate expired card.",
                code=GiftCardErrorCode.EXPIRED_GIFT_CARD,
            )

    @classmethod
    @traced_atomic_transaction()
    def bulk_action(cls, info, queryset):
        queryset = queryset.filter(is_active=False)
        gift_card_ids = [gift_card.id for gift_card in queryset]
        app = load_app(info.context)
        queryset.update(is_active=True)
        events.gift_cards_activated_event(
            gift_card_ids, user=info.context.user, app=app
        )
        manager = load_plugin_manager(info.context)
        for card in models.GiftCard.objects.filter(id__in=gift_card_ids):
            manager.gift_card_status_changed(card)


class GiftCardBulkDeactivate(BaseBulkMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID,
            required=True,
            description="List of gift card IDs to deactivate.",
        )

    class Meta:
        description = "Deactivate gift cards." + ADDED_IN_31 + PREVIEW_FEATURE
        model = models.GiftCard
        object_type = GiftCard
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = GiftCardError

    @classmethod
    @traced_atomic_transaction()
    def bulk_action(cls, info, queryset):
        app = load_app(info.context)
        queryset = queryset.filter(is_active=True)
        gift_card_ids = [gift_card.id for gift_card in queryset]
        queryset.update(is_active=False)
        events.gift_cards_deactivated_event(
            gift_card_ids, user=info.context.user, app=app
        )
        manager = load_plugin_manager(info.context)
        for card in models.GiftCard.objects.filter(id__in=gift_card_ids):
            manager.gift_card_status_changed(card)

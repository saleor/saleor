from copy import deepcopy

import graphene
from django.core.exceptions import ValidationError

from ....core.tracing import traced_atomic_transaction
from ....giftcard import events, models
from ....giftcard.error_codes import GiftCardErrorCode
from ....permission.enums import GiftcardPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_31
from ...core.doc_category import DOC_CATEGORY_GIFT_CARDS
from ...core.scalars import PositiveDecimal
from ...core.types import GiftCardError, NonNullList
from ...core.utils import WebhookEventInfo
from ...core.validators import validate_price_precision
from ...plugins.dataloaders import get_plugin_manager_promise
from ...utils.validators import check_for_duplicates
from ..types import GiftCard
from .gift_card_create import GiftCardCreate, GiftCardInput


class GiftCardUpdateInput(GiftCardInput):
    remove_tags = NonNullList(
        graphene.String,
        description="The gift card tags to remove." + ADDED_IN_31,
    )
    balance_amount = PositiveDecimal(
        description="The gift card balance amount." + ADDED_IN_31,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_GIFT_CARDS


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
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.GIFT_CARD_UPDATED,
                description="A gift card was updated.",
            )
        ]

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
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
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
        app = get_app_promise(info.context).get()
        if "initial_balance_amount" in cleaned_input:
            events.gift_card_balance_reset_event(instance, old_instance, user, app)
        if "expiry_date" in cleaned_input:
            events.gift_card_expiry_date_updated_event(
                instance, old_instance, user, app
            )
        if tags_updated:
            events.gift_card_tags_updated_event(instance, old_tags, user, app)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.gift_card_updated, instance)
        return cls.success_response(instance)

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        cls.clean_tags(cleaned_input)
        return cleaned_input

    @classmethod
    def _save_m2m(cls, info: ResolveInfo, instance, cleaned_data):
        with traced_atomic_transaction():
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

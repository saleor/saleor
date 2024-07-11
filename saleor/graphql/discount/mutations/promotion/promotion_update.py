from datetime import datetime
from typing import Optional

import graphene
import pytz
from django.core.exceptions import ValidationError
from django.db import transaction

from .....discount import PromotionType, events, models
from .....discount.utils.promotion import mark_catalogue_promotion_rules_as_dirty
from .....permission.enums import DiscountPermissions
from .....plugins.manager import PluginsManager
from .....webhook.event_types import WebhookEventAsyncType
from ....app.dataloaders import get_app_promise
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_317, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.mutations import ModelMutation
from ....core.types import Error
from ....core.utils import WebhookEventInfo
from ....core.validators import validate_end_is_after_start
from ....plugins.dataloaders import get_plugin_manager_promise
from ...enums import PromotionUpdateErrorCode
from ...types import Promotion
from ..utils import clear_promotion_old_sale_id
from .promotion_create import PromotionInput

TOGGLE_EVENT = {
    "started": events.promotion_started_event,
    "ended": events.promotion_ended_event,
}


class PromotionUpdateError(Error):
    code = PromotionUpdateErrorCode(description="The error code.", required=True)


class PromotionUpdateInput(PromotionInput):
    name = graphene.String(description="Promotion name.")


class PromotionUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of the promotion to update.")
        input = PromotionUpdateInput(
            description="Fields required to update a promotion.", required=True
        )

    class Meta:
        description = "Updates an existing promotion." + ADDED_IN_317 + PREVIEW_FEATURE
        model = models.Promotion
        object_type = Promotion
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = PromotionUpdateError
        doc_category = DOC_CATEGORY_DISCOUNTS
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.PROMOTION_UPDATED,
                description="A promotion was updated.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.PROMOTION_STARTED,
                description="Optionally called if promotion was started.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.PROMOTION_ENDED,
                description="Optionally called if promotion was ended.",
            ),
        ]

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        instance = cls.get_instance(info, **data)
        previous_end_date = instance.end_date
        data: dict = data["input"]
        cleaned_input: dict = cls.clean_input(info, instance, data)
        with transaction.atomic():
            instance = cls.construct_instance(instance, cleaned_input)
            cls.clean_instance(info, instance)
            clear_promotion_old_sale_id(instance)
            cls.save(info, instance, cleaned_input)
            cls._save_m2m(info, instance, cleaned_input)
            cls.post_save_actions(info, cleaned_input, instance, previous_end_date)
        return cls.success_response(instance)

    @classmethod
    def clean_input(
        cls, info: ResolveInfo, instance: models.Promotion, data: dict, **kwargs
    ):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        start_date = cleaned_input.get("start_date") or instance.start_date
        end_date = cleaned_input.get("end_date") or instance.end_date
        try:
            validate_end_is_after_start(start_date, end_date)
        except ValidationError as error:
            error.code = PromotionUpdateErrorCode.INVALID.value
            raise ValidationError({"endDate": error})
        return cleaned_input

    @classmethod
    def post_save_actions(cls, info, cleaned_input, instance, previous_end_date):
        toggle_type = cls.get_toggle_type(instance, cleaned_input, previous_end_date)
        cls.save_events(info, instance, toggle_type)

        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.promotion_updated, instance)
        cls.send_promotion_toggle_webhook(manager, instance, toggle_type)

        # update the product undiscounted prices for promotion only when
        # start or end date has changed
        if instance.type == PromotionType.CATALOGUE and (
            "start_date" in cleaned_input or "end_date" in cleaned_input
        ):
            cls.call_event(mark_catalogue_promotion_rules_as_dirty, [instance.pk])

    @classmethod
    def get_toggle_type(cls, instance, clean_input, previous_end_date) -> Optional[str]:
        """Check if promotion has started, ended or there was no toggle.

        Promotion toggles when start or end date already passed and the
        notification_date is not set or the last notification was sent before start
        or end date.

        :return: "started" if promotion has started, "ended" if promotion has ended or
        None if there was no toggle.
        """
        now = datetime.now(pytz.utc)
        notification_date = instance.last_notification_scheduled_at
        start_date = clean_input.get("start_date")
        end_date = clean_input.get("end_date")

        if not start_date and not end_date:
            return None

        if (
            start_date
            and start_date <= now
            and (notification_date is None or notification_date < start_date)
            and (not end_date or end_date > now)
        ):
            return "started"

        if (
            end_date
            and end_date <= now
            and (
                (notification_date is None or notification_date < end_date)
                or previous_end_date is None
            )
        ):
            return "ended"
        return None

    @classmethod
    def send_promotion_toggle_webhook(
        cls,
        manager: "PluginsManager",
        instance: models.Promotion,
        toggle_type: Optional[str],
    ):
        """Send a webhook about starting or ending promotion, if it wasn't sent yet."""
        event = None
        if toggle_type == "started":
            event = manager.promotion_started
        if toggle_type == "ended":
            event = manager.promotion_ended
        if event:
            cls.call_event(event, instance)
            instance.last_notification_scheduled_at = datetime.now(pytz.utc)
            instance.save(update_fields=["last_notification_scheduled_at"])

    @classmethod
    def save_events(
        cls,
        info: ResolveInfo,
        instance: models.Promotion,
        toggle_type: Optional[str],
    ):
        app = get_app_promise(info.context).get()
        user = info.context.user
        events.promotion_updated_event(instance, user, app)
        if toggle_type:
            if event_function := TOGGLE_EVENT.get(toggle_type):
                event_function(instance, user, app)

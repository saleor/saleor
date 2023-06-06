from datetime import datetime
from typing import Optional

import graphene
import pytz
from django.core.exceptions import ValidationError
from django.db import transaction

from .....discount import events, models
from .....permission.enums import DiscountPermissions
from .....plugins.manager import PluginsManager
from .....product.tasks import update_products_discounted_prices_of_promotion_task
from ....app.dataloaders import get_app_promise
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_315, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.mutations import ModelMutation
from ....core.types import Error
from ....core.validators import validate_end_is_after_start
from ....plugins.dataloaders import get_plugin_manager_promise
from ...enums import PromotionUpdateErrorCode
from ...types import Promotion
from ..utils import clear_promotion_old_sale_id
from .promotion_create import PromotionInput

EVENT_TYPE = {
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
        description = "Updates an existing promotion." + ADDED_IN_315 + PREVIEW_FEATURE
        model = models.Promotion
        object_type = Promotion
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = PromotionUpdateError
        doc_category = DOC_CATEGORY_DISCOUNTS

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
        start_date = cleaned_input.get("start_date")
        end_date = cleaned_input.get("end_date")
        try:
            validate_end_is_after_start(start_date, end_date)
        except ValidationError as error:
            error.code = PromotionUpdateErrorCode.INVALID.value
            raise ValidationError({"endDate": error})
        return cleaned_input

    @classmethod
    def post_save_actions(cls, info, cleaned_input, instance, previous_end_date):
        # update the product undiscounted prices for promotion only when
        # start or end date has changed
        if "start_date" in cleaned_input or "end_date" in cleaned_input:
            update_products_discounted_prices_of_promotion_task.delay(instance.pk)

        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(
            manager.promotion_updated,
            instance,
        )
        sent_webhook_type = cls.send_promotion_toggle_webhook(
            manager, instance, cleaned_input, previous_end_date
        )
        cls.save_events(info, instance, sent_webhook_type)

    @classmethod
    def send_promotion_toggle_webhook(
        cls,
        manager: "PluginsManager",
        instance: models.Promotion,
        clean_input: dict,
        previous_end_date: datetime,
    ) -> Optional[str]:
        """Send a webhook about starting or ending promotion if it wasn't sent yet.

        Send webhook when the start or end date already passed and the notification_date
        is not set or the last notification was sent before start or end date.

        :return: "started" for promotion_started and "ended" for promotion_ended webhook
        """
        now = datetime.now(pytz.utc)

        notification_date = instance.last_notification_scheduled_at
        start_date = clean_input.get("start_date")
        end_date = clean_input.get("end_date")

        if not start_date and not end_date:
            return None

        send_notification = False
        for date in [start_date, end_date]:
            if (
                date
                and date <= now
                and (notification_date is None or notification_date < date)
            ):
                send_notification = True

        event = None
        if (start_date and start_date <= now) and (not end_date or end_date > now):
            event = manager.promotion_started

        # we always need to notify if the end_date is in the past and previously
        # the end date was not set
        if end_date and end_date <= now and previous_end_date is None:
            event = manager.promotion_ended
            send_notification = True

        if send_notification and event:
            cls.call_event(event, instance)
            instance.last_notification_scheduled_at = now
            instance.save(update_fields=["last_notification_scheduled_at"])
            if event == manager.promotion_started:
                return "started"
            if event == manager.promotion_ended:
                return "ended"
        return None

    @classmethod
    def save_events(
        cls,
        info: ResolveInfo,
        instance: models.Promotion,
        sent_webhook_type: Optional[str],
    ):
        app = get_app_promise(info.context).get()
        user = info.context.user
        events.promotion_updated_event(instance, user, app)
        if sent_webhook_type:
            if event_function := EVENT_TYPE.get(sent_webhook_type):
                event_function(instance, user, app)

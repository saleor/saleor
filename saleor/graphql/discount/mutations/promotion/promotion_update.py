from datetime import datetime

import graphene
import pytz
from django.core.exceptions import ValidationError
from django.db import transaction

from .....discount import models
from .....permission.enums import DiscountPermissions
from .....plugins.manager import PluginsManager
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_315, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.mutations import ModelMutation
from ....core.types import Error
from ....core.validators import validate_end_is_after_start
from ....plugins.dataloaders import get_plugin_manager_promise
from ...enums import PromotionUpdateErrorCode
from ...types import Promotion
from .promotion_create import PromotionInput


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
        manager = get_plugin_manager_promise(info.context).get()
        cleaned_input: dict = cls.clean_input(info, instance, data)
        with transaction.atomic():
            instance = cls.construct_instance(instance, cleaned_input)
            cls.clean_instance(info, instance)
            cls.save(info, instance, cleaned_input)
            cls._save_m2m(info, instance, cleaned_input)
            cls.send_promotion_webhooks(
                manager, instance, cleaned_input, previous_end_date
            )
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
    def send_promotion_webhooks(
        cls,
        manager: "PluginsManager",
        instance: models.Promotion,
        cleaned_input: dict,
        previous_end_date: datetime,
    ):
        cls.call_event(
            manager.promotion_updated,
            instance,
        )
        cls.send_promotion_toggle_webhook(
            manager, instance, cleaned_input, previous_end_date
        )

    @classmethod
    def send_promotion_toggle_webhook(
        cls,
        manager: "PluginsManager",
        instance: models.Promotion,
        clean_input: dict,
        previous_end_date: datetime,
    ):
        """Send a webhook about starting or ending promotion if it wasn't sent yet.

        Send webhook when the start or end date already passed and the notification_date
        is not set or the last notification was sent before start or end date.
        """
        now = datetime.now(pytz.utc)

        notification_date = instance.last_notification_scheduled_at
        start_date = clean_input.get("start_date")
        end_date = clean_input.get("end_date")

        if not start_date and not end_date:
            return

        send_notification = False
        for date in [start_date, end_date]:
            if (
                date
                and date <= now
                and (notification_date is None or notification_date < date)
            ):
                send_notification = True

        # we always need to notify if the end_date is in the past and previously
        # the end date was not set
        if end_date and end_date <= now and previous_end_date is None:
            send_notification = True

        if send_notification:
            cls.call_event(
                manager.promotion_toggle,
                instance,
            )
            instance.last_notification_scheduled_at = now
            instance.save(update_fields=["last_notification_scheduled_at"])

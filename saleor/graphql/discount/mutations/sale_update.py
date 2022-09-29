from datetime import datetime

import graphene
import pytz

from ....core.permissions import DiscountPermissions
from ....core.tracing import traced_atomic_transaction
from ....discount import models
from ....discount.utils import fetch_catalogue_info
from ...core.mutations import ModelMutation
from ...core.types import DiscountError
from ...plugins.dataloaders import load_plugin_manager
from ..types import Sale
from .sale_create import SaleInput, SaleUpdateDiscountedPriceMixin
from .utils import convert_catalogue_info_to_global_ids


class SaleUpdate(SaleUpdateDiscountedPriceMixin, ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a sale to update.")
        input = SaleInput(
            required=True, description="Fields required to update a sale."
        )

    class Meta:
        description = "Updates a sale."
        model = models.Sale
        object_type = Sale
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        instance = cls.get_instance(info, **data)
        previous_catalogue = fetch_catalogue_info(instance)
        previous_end_date = instance.end_date
        data = data.get("input")
        manager = load_plugin_manager(info.context)
        cleaned_input = cls.clean_input(info, instance, data)
        with traced_atomic_transaction():
            instance = cls.construct_instance(instance, cleaned_input)
            cls.clean_instance(info, instance)
            cls.save(info, instance, cleaned_input)
            cls._save_m2m(info, instance, cleaned_input)
            cls.send_sale_notifications(
                manager, instance, cleaned_input, previous_catalogue, previous_end_date
            )
        return cls.success_response(instance)

    @classmethod
    def send_sale_notifications(
        cls, manager, instance, cleaned_input, previous_catalogue, previous_end_date
    ):
        current_catalogue = convert_catalogue_info_to_global_ids(
            fetch_catalogue_info(instance)
        )
        cls.call_event(
            manager.sale_updated,
            instance,
            convert_catalogue_info_to_global_ids(previous_catalogue),
            current_catalogue,
        )

        cls.send_sale_toggle_notification(
            manager, instance, cleaned_input, current_catalogue, previous_end_date
        )

    @staticmethod
    def send_sale_toggle_notification(
        manager, instance, clean_input, catalogue, previous_end_date
    ):
        """Send the notification about starting or ending sale if it wasn't sent yet.

        Send notification if the notification when the start or end date already passed
        and the notification_date is not set or the last notification was sent
        before start or end date.
        """
        now = datetime.now(pytz.utc)

        notification_date = instance.notification_sent_datetime
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
            manager.sale_toggle(instance, catalogue)
            instance.notification_sent_datetime = now
            instance.save(update_fields=["notification_sent_datetime"])

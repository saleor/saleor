from datetime import datetime

import graphene
import pytz
from django.db import transaction

from ....core.permissions import DiscountPermissions
from ....core.tracing import traced_atomic_transaction
from ....discount import models
from ....discount.utils import fetch_catalogue_info
from ...core.mutations import ModelMutation
from ...core.types import DiscountError
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
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        instance = cls.get_instance(info, **data)
        previous_catalogue = fetch_catalogue_info(instance)
        data = data.get("input")
        cleaned_input = cls.clean_input(info, instance, data)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(info, instance)
        cls.save(info, instance, cleaned_input)
        cls._save_m2m(info, instance, cleaned_input)
        cls.send_sale_notifications(info, instance, cleaned_input, previous_catalogue)
        return cls.success_response(instance)

    @classmethod
    def clean_input(cls, info, instance, data, input_cls=None):
        clean_input = super().clean_input(info, instance, data)
        cls.update_notification_flag_if_needed(instance, clean_input)
        return clean_input

    @staticmethod
    def update_notification_flag_if_needed(instance, clean_input):
        """Update a notification flag when the date is in the feature.

        Set the notification flag to False when the starting or ending date change
        to the feature date.
        """
        now = datetime.now(pytz.utc)
        for field in ["start", "end"]:
            notification_field = f"{field}ed_notification_sent"
            date = clean_input.get(f"{field}_date")
            if date and getattr(instance, notification_field) and date > now:
                clean_input[notification_field] = False

    @classmethod
    def send_sale_notifications(cls, info, instance, cleaned_input, previous_catalogue):
        current_catalogue = convert_catalogue_info_to_global_ids(
            fetch_catalogue_info(instance)
        )
        transaction.on_commit(
            lambda: info.context.plugins.sale_updated(
                instance,
                convert_catalogue_info_to_global_ids(previous_catalogue),
                current_catalogue,
            )
        )

        cls.send_sale_started_or_ended_notification(
            info, instance, cleaned_input, current_catalogue
        )

    @staticmethod
    def send_sale_started_or_ended_notification(info, instance, clean_input, catalogue):
        """Send the notification about starting or ending sale if it wasn't sent yet.

        Send notification if the notification field is set to False and the starting
        or ending date already passed.
        """
        manager = info.context.plugins
        now = datetime.now(pytz.utc)
        update_fields = []
        for field in ["start", "end"]:
            notification_field = f"{field}ed_notification_sent"
            date = clean_input.get(f"{field}_date")
            if date and not getattr(instance, notification_field) and date <= now:
                if field == "start":
                    manager.sale_started(instance, catalogue)
                else:
                    manager.sale_ended(instance, catalogue)
                setattr(instance, notification_field, True)
                update_fields.append(notification_field)
        if update_fields:
            instance.save(update_fields=update_fields)

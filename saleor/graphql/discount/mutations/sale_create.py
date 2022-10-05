from datetime import datetime

import graphene
import pytz
from django.core.exceptions import ValidationError

from ....core.permissions import DiscountPermissions
from ....core.tracing import traced_atomic_transaction
from ....discount import models
from ....discount.error_codes import DiscountErrorCode
from ....discount.utils import fetch_catalogue_info
from ....product.tasks import update_products_discounted_prices_of_discount_task
from ...channel import ChannelContext
from ...core.descriptions import ADDED_IN_31
from ...core.mutations import ModelMutation
from ...core.scalars import PositiveDecimal
from ...core.types import DiscountError, NonNullList
from ...core.validators import validate_end_is_after_start
from ...plugins.dataloaders import load_plugin_manager
from ..enums import DiscountValueTypeEnum
from ..types import Sale
from .utils import convert_catalogue_info_to_global_ids


class SaleUpdateDiscountedPriceMixin:
    @classmethod
    def success_response(cls, instance):
        # Update the "discounted_prices" of the associated, discounted
        # products (including collections and categories).
        update_products_discounted_prices_of_discount_task.delay(instance.pk)
        return super().success_response(
            ChannelContext(node=instance, channel_slug=None)
        )


class SaleInput(graphene.InputObjectType):
    name = graphene.String(description="Voucher name.")
    type = DiscountValueTypeEnum(description="Fixed or percentage.")
    value = PositiveDecimal(description="Value of the voucher.")
    products = NonNullList(
        graphene.ID, description="Products related to the discount.", name="products"
    )
    variants = NonNullList(
        graphene.ID,
        descriptions="Product variant related to the discount." + ADDED_IN_31,
        name="variants",
    )
    categories = NonNullList(
        graphene.ID,
        description="Categories related to the discount.",
        name="categories",
    )
    collections = NonNullList(
        graphene.ID,
        description="Collections related to the discount.",
        name="collections",
    )
    start_date = graphene.types.datetime.DateTime(
        description="Start date of the voucher in ISO 8601 format."
    )
    end_date = graphene.types.datetime.DateTime(
        description="End date of the voucher in ISO 8601 format."
    )


class SaleCreate(SaleUpdateDiscountedPriceMixin, ModelMutation):
    class Arguments:
        input = SaleInput(
            required=True, description="Fields required to create a sale."
        )

    class Meta:
        description = "Creates a new sale."
        model = models.Sale
        object_type = Sale
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    def clean_instance(cls, info, instance):
        super().clean_instance(info, instance)
        start_date = instance.start_date
        end_date = instance.end_date
        try:
            validate_end_is_after_start(start_date, end_date)
        except ValidationError as error:
            error.code = DiscountErrorCode.INVALID.value
            raise ValidationError({"end_date": error})

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        with traced_atomic_transaction():
            response = super().perform_mutation(_root, info, **data)
            instance = getattr(response, cls._meta.return_field_name).node
            manager = load_plugin_manager(info.context)
            cls.send_sale_notifications(manager, instance)
        return response

    @classmethod
    def send_sale_notifications(cls, manager, instance):
        current_catalogue = convert_catalogue_info_to_global_ids(
            fetch_catalogue_info(instance)
        )

        cls.call_event(manager.sale_created, instance, current_catalogue)
        cls.send_sale_toggle_notification(manager, instance, current_catalogue)

    @staticmethod
    def send_sale_toggle_notification(manager, instance, catalogue):
        """Send a notification about starting or ending sale if it hasn't been sent yet.

        Send the notification when the start date is before the current date and the
        sale is not already finished.
        """
        now = datetime.now(pytz.utc)

        start_date = instance.start_date
        end_date = instance.end_date

        if (start_date and start_date <= now) and (not end_date or not end_date <= now):
            manager.sale_toggle(instance, catalogue)
            instance.notification_sent_datetime = now
            instance.save(update_fields=["notification_sent_datetime"])

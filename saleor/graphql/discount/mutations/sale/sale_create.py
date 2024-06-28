from datetime import datetime

import graphene
import pytz
from django.core.exceptions import ValidationError

from .....core.tracing import traced_atomic_transaction
from .....discount import PromotionType, models
from .....discount.error_codes import DiscountErrorCode
from .....discount.models import Promotion
from .....discount.utils.promotion import mark_catalogue_promotion_rules_as_dirty
from .....permission.enums import DiscountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....channel import ChannelContext
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_31, DEPRECATED_IN_3X_MUTATION
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.mutations import ModelMutation
from ....core.scalars import DateTime, PositiveDecimal
from ....core.types import BaseInputObjectType, DiscountError, NonNullList
from ....core.utils import WebhookEventInfo
from ....core.validators import validate_end_is_after_start
from ....plugins.dataloaders import get_plugin_manager_promise
from ...enums import DiscountValueTypeEnum
from ...types import Sale
from ...utils import (
    convert_migrated_sale_predicate_to_catalogue_info,
    create_catalogue_predicate,
)


class SaleInput(BaseInputObjectType):
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
    start_date = DateTime(description="Start date of the voucher in ISO 8601 format.")
    end_date = DateTime(description="End date of the voucher in ISO 8601 format.")

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS


class SaleCreate(ModelMutation):
    class Arguments:
        input = SaleInput(
            required=True, description="Fields required to create a sale."
        )

    class Meta:
        description = (
            "Creates a new sale."
            + DEPRECATED_IN_3X_MUTATION
            + " Use `promotionCreate` mutation instead."
        )
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        model = models.Promotion
        object_type = Sale
        return_field_name = "sale"
        error_type_class = DiscountError
        error_type_field = "discount_errors"
        doc_category = DOC_CATEGORY_DISCOUNTS
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.SALE_CREATED,
                description="A sale was created.",
            ),
        ]

    @classmethod
    def create_predicate(cls, input):
        collections = input.get("collections")
        categories = input.get("categories")
        products = input.get("products")
        variants = input.get("variants")

        return create_catalogue_predicate(collections, categories, products, variants)

    @classmethod
    def success_response(cls, instance):
        return super().success_response(
            ChannelContext(node=instance, channel_slug=None)
        )

    @classmethod
    def clean_instance(cls, info: ResolveInfo, instance):
        super().clean_instance(info, instance)
        start_date = instance.start_date
        end_date = instance.end_date
        try:
            validate_end_is_after_start(start_date, end_date)
        except ValidationError as error:
            error.code = DiscountErrorCode.INVALID.value
            raise ValidationError({"end_date": error})

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        with traced_atomic_transaction():
            input = data["input"]
            reward_value_type = input.pop("type", None)
            response = super().perform_mutation(_root, info, **data)
            promotion: Promotion = response.sale.node
            promotion.assign_old_sale_id()
            promotion.type = PromotionType.CATALOGUE
            predicate = cls.create_predicate(input)
            models.PromotionRule.objects.create(
                name="",
                promotion=promotion,
                catalogue_predicate=predicate,
                reward_value_type=reward_value_type,
            )
            manager = get_plugin_manager_promise(info.context).get()
            cls.send_sale_notifications(manager, promotion, predicate)
            cls.call_event(mark_catalogue_promotion_rules_as_dirty, [promotion.pk])
        return response

    @classmethod
    def send_sale_notifications(cls, manager, instance, predicate):
        catalogue_info = convert_migrated_sale_predicate_to_catalogue_info(predicate)
        cls.call_event(manager.sale_created, instance, catalogue_info)
        cls.send_sale_toggle_notification(manager, instance, catalogue_info)

    @classmethod
    def send_sale_toggle_notification(cls, manager, instance, catalogue):
        """Send a notification about starting or ending sale if it hasn't been sent yet.

        Send the notification when the start date is before the current date and the
        sale is not already finished.
        """
        now = datetime.now(pytz.utc)

        start_date = instance.start_date
        end_date = instance.end_date

        if (start_date and start_date <= now) and (not end_date or not end_date <= now):
            cls.call_event(manager.sale_toggle, instance, catalogue)
            instance.last_notification_scheduled_at = now
            instance.save(update_fields=["last_notification_scheduled_at"])

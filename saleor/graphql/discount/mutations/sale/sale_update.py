from datetime import datetime

import graphene
import pytz
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef

from .....core.tracing import traced_atomic_transaction
from .....discount import models
from .....discount.error_codes import DiscountErrorCode
from .....discount.utils.promotion import CATALOGUE_FIELDS
from .....permission.enums import DiscountPermissions
from .....product import models as product_models
from .....product.utils.product import mark_products_in_channels_as_dirty
from .....webhook.event_types import WebhookEventAsyncType
from ....channel import ChannelContext
from ....core import ResolveInfo
from ....core.descriptions import DEPRECATED_IN_3X_MUTATION
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.mutations import ModelMutation
from ....core.types import DiscountError
from ....core.utils import (
    WebhookEventInfo,
    from_global_id_or_error,
    raise_validation_error,
)
from ....core.validators import validate_end_is_after_start
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Sale
from ...utils import (
    convert_migrated_sale_predicate_to_catalogue_info,
    create_catalogue_predicate,
    get_products_for_rule,
    get_variants_for_catalogue_predicate,
)
from ..utils import update_variants_for_promotion
from .sale_create import SaleInput


class SaleUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a sale to update.")
        input = SaleInput(
            required=True, description="Fields required to update a sale."
        )

    class Meta:
        description = (
            "Updates a sale."
            + DEPRECATED_IN_3X_MUTATION
            + " Use `promotionUpdate` mutation instead."
        )
        model = models.Promotion
        object_type = Sale
        return_field_name = "sale"
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"
        doc_category = DOC_CATEGORY_DISCOUNTS
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.SALE_UPDATED,
                description="A sale was updated.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.SALE_TOGGLE,
                description="Optionally triggered when a sale is started or stopped.",
            ),
        ]

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        promotion = cls.get_instance(info, **data)
        input = data.get("input")
        cls.validate_dates(promotion, input)
        rules = promotion.rules.all()
        previous_predicate = rules[0].catalogue_predicate
        previous_catalogue = convert_migrated_sale_predicate_to_catalogue_info(
            previous_predicate
        )
        previous_end_date = promotion.end_date
        previous_products = get_products_for_rule(rules[0])
        previous_product_ids = set(previous_products.values_list("id", flat=True))
        with traced_atomic_transaction():
            cls.update_fields(promotion, rules, input)
            cls.clean_instance(info, promotion)
            promotion.save()
            for rule in rules:
                cls.clean_instance(info, rule)
                rule.save()

            cls.post_save_actions(
                info,
                input,
                promotion,
                previous_catalogue,
                previous_end_date,
                previous_product_ids,
            )

        return cls.success_response(ChannelContext(node=promotion, channel_slug=None))

    @classmethod
    def get_instance(cls, info: ResolveInfo, **data):
        type, _id = from_global_id_or_error(data["id"], raise_error=False)
        if type == "Promotion":
            raise_validation_error(
                field="id",
                message="Provided ID refers to Promotion model. "
                "Please use 'promotionUpdate' mutation instead.",
                code=DiscountErrorCode.INVALID.value,
            )
        object_id = cls.get_global_id_or_error(data["id"], "Sale")
        try:
            return models.Promotion.objects.get(old_sale_id=object_id)
        except models.Promotion.DoesNotExist:
            raise_validation_error(
                field="id",
                message="Sale with given ID can't be found.",
                code=DiscountErrorCode.NOT_FOUND,
            )

    @staticmethod
    def validate_dates(instance, input):
        start_date = input.get("start_date") or instance.start_date
        end_date = input.get("end_date") or instance.end_date
        try:
            validate_end_is_after_start(start_date, end_date)
        except ValidationError as error:
            error.code = DiscountErrorCode.INVALID.value
            raise ValidationError({"end_date": error})

    @classmethod
    def update_fields(
        cls, promotion: models.Promotion, rules: list[models.PromotionRule], input
    ):
        if name := input.get("name"):
            promotion.name = name
        if start_date := input.get("start_date"):
            promotion.start_date = start_date
        if "end_date" in input.keys():
            end_date = input.get("end_date")
            promotion.end_date = end_date

        # We need to make sure, that all rules have the same type and predicate
        if type := input.get("type"):
            for rule in rules:
                rule.reward_value_type = type

        if any([key in CATALOGUE_FIELDS for key in input.keys()]):
            predicate = cls.create_predicate(input)
            for rule in rules:
                rule.catalogue_predicate = predicate

    @staticmethod
    def create_predicate(input):
        collections = input.get("collections")
        categories = input.get("categories")
        products = input.get("products")
        variants = input.get("variants")

        return create_catalogue_predicate(collections, categories, products, variants)

    @classmethod
    def post_save_actions(
        cls,
        info,
        input,
        promotion,
        previous_catalogue,
        previous_end_date,
        previous_product_ids,
    ):
        rule = promotion.rules.first()
        channel_ids = rule.channels.values_list("id", flat=True)
        current_predicate = rule.catalogue_predicate
        current_catalogue = convert_migrated_sale_predicate_to_catalogue_info(
            current_predicate
        )
        manager = get_plugin_manager_promise(info.context).get()
        cls.send_sale_notifications(
            manager,
            promotion,
            input,
            previous_catalogue,
            current_catalogue,
            previous_end_date,
        )
        if any(
            field in input.keys()
            for field in [*CATALOGUE_FIELDS, "start_date", "end_date", "type"]
        ):
            variants = get_variants_for_catalogue_predicate(current_predicate)
            product_ids = set(
                product_models.Product.objects.filter(
                    Exists(variants.filter(product_id=OuterRef("id")))
                ).values_list("id", flat=True)
            )
            update_variants_for_promotion(variants, promotion)
            if product_ids | previous_product_ids:
                product_ids_to_update = product_ids | previous_product_ids
                cls.call_event(
                    mark_products_in_channels_as_dirty,
                    {channel_id: product_ids_to_update for channel_id in channel_ids},
                )

    @classmethod
    def send_sale_notifications(
        cls,
        manager,
        instance,
        input,
        previous_catalogue,
        current_catalogue,
        previous_end_date,
    ):
        cls.call_event(
            manager.sale_updated,
            instance,
            previous_catalogue,
            current_catalogue,
        )

        cls.send_sale_toggle_notification(
            manager, instance, input, current_catalogue, previous_end_date
        )

    @classmethod
    def send_sale_toggle_notification(
        cls, manager, instance, input, catalogue, previous_end_date
    ):
        """Send the notification about starting or ending sale if it wasn't sent yet.

        Send notification if the notification when the start or end date already passed
        and the notification_date is not set or the last notification was sent
        before start or end date.
        """
        now = datetime.now(pytz.utc)

        notification_date = instance.last_notification_scheduled_at
        start_date = input.get("start_date")
        end_date = input.get("end_date")

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
            cls.call_event(manager.sale_toggle, instance, catalogue)
            instance.last_notification_scheduled_at = now
            instance.save(update_fields=["last_notification_scheduled_at"])

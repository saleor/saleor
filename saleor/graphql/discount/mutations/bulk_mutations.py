import graphene
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import OuterRef, Subquery

from ....discount import models
from ....discount.error_codes import DiscountErrorCode
from ....discount.models import VoucherCode
from ....permission.enums import DiscountPermissions
from ....product.utils.product import (
    get_channel_to_products_map_from_rules,
    mark_products_in_channels_as_dirty,
)
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.utils import get_webhooks_for_event
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_DISCOUNTS
from ...core.mutations import ModelBulkDeleteMutation
from ...core.types import DiscountError, NonNullList
from ...core.utils import (
    WebhookEventInfo,
    from_global_id_or_error,
    raise_validation_error,
)
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Sale, Voucher
from ..utils import convert_migrated_sale_predicate_to_catalogue_info


class SaleBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of sale IDs to delete."
        )

    class Meta:
        description = "Deletes sales."
        model = models.Promotion
        object_type = Sale
        return_field_name = "sale"
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"
        doc_category = DOC_CATEGORY_DISCOUNTS
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.SALE_DELETED,
                description="A sale was deleted.",
            )
        ]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, ids, **data
    ) -> tuple[int, ValidationError | None]:
        """Perform a mutation that deletes a list of model instances."""
        try:
            instances = cls.get_promotion_instances(ids)
        except ValidationError as error:
            return 0, error

        count = len(instances)
        if count:
            cls.bulk_action(info, instances, **data)
        return count, None

    @classmethod
    def get_promotion_instances(cls, ids):
        invalid_ids = []
        for id in ids:
            type, _id = from_global_id_or_error(id, raise_error=False)
            if type == "Promotion":
                invalid_ids.append(id)

        if invalid_ids:
            raise_validation_error(
                field="id",
                message="Provided IDs refer to Promotion model. "
                "Please use 'promotionBulkDelete' mutation instead.",
                code=DiscountErrorCode.INVALID.value,
            )
        pks = cls.get_global_ids_or_error(ids, "Sale")
        return models.Promotion.objects.filter(old_sale_id__in=pks)

    @classmethod
    def bulk_action(cls, info: ResolveInfo, queryset, /):
        with transaction.atomic():
            promotions = tuple(
                models.Promotion.objects.order_by("pk")
                .select_for_update(of=("self",))
                .filter(pk__in=queryset.values_list("pk", flat=True))
            )
            rules = cls.get_sales(promotions)
            sale_id_to_rule = cls.get_sale_and_rules(rules)
            sales_and_catalogue_infos = [
                (promotion, cls.get_catalogue_info(sale_id_to_rule.get(promotion.id)))
                for promotion in promotions
            ]
            channel_to_products_map = cls.get_channel_to_products_map(rules)

            models.PromotionRule.objects.order_by("pk").filter(
                pk__in=[rule.pk for rule in rules]
            ).delete()
            models.Promotion.objects.order_by("pk").filter(
                pk__in=[promotion.pk for promotion in promotions]
            ).delete()

        webhooks = get_webhooks_for_event(WebhookEventAsyncType.SALE_DELETED)
        manager = get_plugin_manager_promise(info.context).get()
        for sale, catalogue_info in sales_and_catalogue_infos:
            cls.call_event(
                manager.sale_deleted, sale, catalogue_info, webhooks=webhooks
            )
        if channel_to_products_map:
            cls.call_event(mark_products_in_channels_as_dirty, channel_to_products_map)

    @classmethod
    def get_sale_and_rules(cls, rules: tuple[models.PromotionRule, ...]):
        return {rule.promotion_id: rule for rule in rules}

    @classmethod
    def get_catalogue_info(cls, rule: models.PromotionRule):
        return convert_migrated_sale_predicate_to_catalogue_info(
            rule.catalogue_predicate
        )

    @classmethod
    def get_channel_to_products_map(cls, rules: tuple[models.PromotionRule, ...]):
        rules = models.PromotionRule.objects.order_by("pk").filter(
            pk__in=[rule.pk for rule in rules]
        )
        return get_channel_to_products_map_from_rules(rules)

    @classmethod
    def get_sales(cls, promotions) -> tuple[models.PromotionRule, ...]:
        return tuple(
            models.PromotionRule.objects.order_by("pk")
            .select_for_update(of=("self",))
            .filter(promotion_id__in=[promotion.pk for promotion in promotions])
        )


class VoucherBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of voucher IDs to delete."
        )

    class Meta:
        description = "Deletes vouchers."
        model = models.Voucher
        object_type = Voucher
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.VOUCHER_DELETED,
                description="A voucher was deleted.",
            )
        ]

    @classmethod
    def bulk_action(cls, info: ResolveInfo, queryset, /):
        manager = get_plugin_manager_promise(info.context).get()
        vouchers = queryset.annotate(
            last_code=Subquery(
                VoucherCode.objects.filter(voucher=OuterRef("pk")).values("code")[:1]
            )
        )
        codes = [voucher.last_code for voucher in vouchers]
        webhooks = get_webhooks_for_event(WebhookEventAsyncType.VOUCHER_DELETED)
        queryset.delete()

        for voucher, code in zip(vouchers, codes, strict=False):
            cls.call_event(manager.voucher_deleted, voucher, code, webhooks=webhooks)

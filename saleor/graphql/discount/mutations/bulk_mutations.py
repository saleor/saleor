from typing import Optional

import graphene
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef, QuerySet

from ....discount import models
from ....discount.error_codes import DiscountErrorCode
from ....permission.enums import DiscountPermissions
from ....product import models as product_models
from ....product.tasks import update_products_discounted_prices_for_promotion_task
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
from ..utils import (
    convert_migrated_sale_predicate_to_catalogue_info,
    get_variants_for_predicate,
)


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
    ) -> tuple[int, Optional[ValidationError]]:
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
        sale_id_to_rule = cls.get_sale_and_rules(queryset)
        sales_and_catalogue_infos = [
            (sale, cls.get_catalogue_info(sale_id_to_rule.get(sale.id)))
            for sale in queryset
        ]
        product_ids = cls.get_product_ids(sale_id_to_rule)

        queryset.delete()

        webhooks = get_webhooks_for_event(WebhookEventAsyncType.SALE_DELETED)
        manager = get_plugin_manager_promise(info.context).get()
        for sale, catalogue_info in sales_and_catalogue_infos:
            cls.call_event(
                manager.sale_deleted, sale, catalogue_info, webhooks=webhooks
            )

        update_products_discounted_prices_for_promotion_task.delay(list(product_ids))

    @classmethod
    def get_sale_and_rules(cls, qs: QuerySet[models.Promotion]):
        rules = models.PromotionRule.objects.filter(
            Exists(qs.filter(id=OuterRef("promotion_id")))
        )
        sale_id_to_rule = {rule.promotion_id: rule for rule in rules}
        return sale_id_to_rule

    @classmethod
    def get_catalogue_info(cls, rule: models.PromotionRule):
        return convert_migrated_sale_predicate_to_catalogue_info(
            rule.catalogue_predicate
        )

    @classmethod
    def get_product_ids(cls, get_sale_and_rules: dict):
        variants = product_models.ProductVariant.objects.none()
        for rule in get_sale_and_rules.values():
            variants |= get_variants_for_predicate(rule.catalogue_predicate)

        products = product_models.Product.objects.filter(
            Exists(variants.filter(product_id=OuterRef("id")))
        )
        return set(products.values_list("id", flat=True))


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
        vouchers = list(queryset)
        codes = [voucher.code for voucher in vouchers]
        webhooks = get_webhooks_for_event(WebhookEventAsyncType.VOUCHER_DELETED)
        queryset.delete()

        for voucher, code in zip(vouchers, codes):
            cls.call_event(manager.voucher_deleted, voucher, code, webhooks=webhooks)

from collections import defaultdict

import graphene

from ....discount import models
from ....discount.utils import CATALOGUE_FIELDS, fetch_catalogue_info
from ....permission.enums import DiscountPermissions
from ....product.tasks import update_products_discounted_prices_of_catalogues_task
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.mutations import ModelBulkDeleteMutation
from ...core.types import DiscountError, NonNullList
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Sale, Voucher
from .utils import convert_catalogue_info_to_global_ids


class SaleBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of sale IDs to delete."
        )

    class Meta:
        description = "Deletes sales."
        model = models.Sale
        object_type = Sale
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.SALE_DELETED,
                description="A sale was deleted.",
            )
        ]

    @classmethod
    def bulk_action(cls, info: ResolveInfo, queryset, /):
        sales_and_catalogue_infos = [
            (sale, fetch_catalogue_info(sale)) for sale in queryset
        ]

        queryset.delete()

        catalogues_to_recalculate = defaultdict(set)
        manager = get_plugin_manager_promise(info.context).get()
        for sale, catalogue_info in sales_and_catalogue_infos:
            manager.sale_deleted(
                sale, convert_catalogue_info_to_global_ids(catalogue_info)
            )
            for field in CATALOGUE_FIELDS:
                catalogues_to_recalculate[field].update(catalogue_info[field])

        update_products_discounted_prices_of_catalogues_task.delay(
            product_ids=list(catalogues_to_recalculate["products"]),
            category_ids=list(catalogues_to_recalculate["categories"]),
            collection_ids=list(catalogues_to_recalculate["collections"]),
            variant_ids=list(catalogues_to_recalculate["variants"]),
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
        vouchers = list(queryset)
        queryset.delete()
        manager = get_plugin_manager_promise(info.context).get()
        for voucher in vouchers:
            manager.voucher_deleted(voucher)

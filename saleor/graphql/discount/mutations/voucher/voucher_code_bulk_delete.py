import graphene

from .....discount import models
from .....permission.enums import DiscountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_318
from ....core.mutations import ModelBulkDeleteMutation
from ....core.types import DiscountError, NonNullList
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import VoucherCode


class VoucherCodeBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID,
            required=True,
            description="List of voucher codes IDs to delete.",
        )

    class Meta:
        description = "Deletes voucher codes." + ADDED_IN_318
        model = models.VoucherCode
        object_type = VoucherCode
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.VOUCHER_UPDATED,
                description="A voucher was updated.",
            )
        ]

    @classmethod
    def bulk_action(cls, info: ResolveInfo, queryset, /):
        manager = get_plugin_manager_promise(info.context).get()
        vouchers = {code.voucher for code in queryset}

        queryset.delete()

        for voucher in vouchers:
            cls.call_event(manager.voucher_updated, voucher, "")

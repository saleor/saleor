import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from .....discount import models
from .....discount.error_codes import DiscountErrorCode
from .....permission.enums import DiscountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....core import ResolveInfo
from ....core.types import DiscountError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Voucher
from .voucher_create import VoucherCreate, VoucherInput


class VoucherUpdate(VoucherCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a voucher to update.")
        input = VoucherInput(
            required=True, description="Fields required to update a voucher."
        )

    class Meta:
        description = "Updates a voucher."
        model = models.Voucher
        object_type = Voucher
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
    def construct_codes_instances(cls, code, codes_data, usage_limit, voucher_instance):
        if codes_data:
            return [
                models.VoucherCode(
                    code=code_data["code"],
                    usage_limit=usage_limit,
                    voucher=voucher_instance,
                )
                for code_data in codes_data
            ]

        if code:
            if voucher_instance.codes.count() == 1:
                code_instance = voucher_instance.codes.first()
                code_instance.code = code

                if usage_limit is not None:
                    code_instance.usage_limit = usage_limit

                return [code_instance]
            else:
                raise ValidationError(
                    {
                        "code": ValidationError(
                            "Cannot update code when multiple codes exists.",
                            code=DiscountErrorCode.INVALID.value,
                        )
                    }
                )

    @classmethod
    def save(
        cls, _info: ResolveInfo, voucher_instance, code_instances, has_multiple_codes
    ):
        codes_to_create = []
        codes_to_update = []

        if has_multiple_codes:
            codes_to_create += code_instances
        else:
            codes_to_update += code_instances

        with transaction.atomic():
            voucher_instance.save()
            models.VoucherCode.objects.bulk_create(codes_to_create)
            models.VoucherCode.objects.bulk_update(
                codes_to_update, fields=["code", "usage_limit"]
            )

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, code):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.voucher_updated, instance, code)

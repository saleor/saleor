from collections import Counter
from itertools import chain

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Exists, OuterRef, Q

from .....checkout import models as checkout_models
from .....discount import models
from .....discount.error_codes import DiscountErrorCode
from .....order import OrderStatus
from .....order import models as order_models
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
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.VOUCHER_CODES_CREATED,
                description="A voucher code was created.",
            ),
        ]

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cls.clean_codes(data)
        cls.clean_voucher_usage_setting(instance, data)
        cls.clean_usage_limit(instance, data)
        cleaned_input = super().clean_input(info, instance, data, **kwargs)

        return cleaned_input

    @classmethod
    def clean_codes(cls, data):
        if "code" in data:
            cls._clean_old_code(data)

        if "add_codes" in data:
            cls._clean_new_codes(data)

    @classmethod
    def clean_voucher_usage_setting(cls, instance, data):
        """Ensure single use setting is not changed if voucher was already used."""
        if "single_use" in data and instance.single_use != data["single_use"]:
            voucher_codes = instance.codes.all()
            used_codes = voucher_codes.filter(
                Exists(order_models.Order.objects.filter(voucher_code=OuterRef("code")))
                | Exists(
                    order_models.OrderLine.objects.filter(voucher_code=OuterRef("code"))
                )
                | Exists(
                    checkout_models.Checkout.objects.filter(
                        voucher_code=OuterRef("code")
                    )
                )
            )
            if used_codes.exists():
                raise ValidationError(
                    {
                        "single_use": ValidationError(
                            "Cannot change single use setting when any voucher code has "
                            "already been used.",
                            code=DiscountErrorCode.VOUCHER_ALREADY_USED.value,
                        )
                    }
                )

    @classmethod
    def count_voucher_usage(cls, voucher: Voucher) -> dict[str, int]:
        voucher_codes = [code.code for code in voucher.codes.all()]
        orders = order_models.Order.objects.select_related("channel").filter(
            voucher_code__in=voucher_codes
        )
        orders = orders.exclude(
            Q(channel__include_draft_order_in_voucher_usage=False)
            & Q(status=OrderStatus.DRAFT)
        ).values_list("voucher_code", flat=True)
        order_lines = order_models.OrderLine.objects.select_related(
            "order__channel"
        ).filter(voucher_code__in=voucher_codes)
        order_lines = order_lines.exclude(
            Q(order__channel__include_draft_order_in_voucher_usage=False)
            & Q(order__status=OrderStatus.DRAFT)
        ).values_list("voucher_code", flat=True)
        checkouts = checkout_models.Checkout.objects.filter(
            voucher_code__in=voucher_codes
        ).values_list("voucher_code", flat=True)

        usage = list(chain(orders, order_lines, checkouts))
        return dict(Counter(usage))  # type: ignore[arg-type]

    @classmethod
    def clean_usage_limit(cls, instance: Voucher, data):
        if "usage_limit" in data and instance.usage_limit != data["usage_limit"]:
            new_limit = data["usage_limit"]
            current_usage_data = cls.count_voucher_usage(instance)
            current_usage_total = sum(current_usage_data.values())
            if current_usage_total > new_limit:
                raise ValidationError(
                    {
                        "usage_limit": ValidationError(
                            "The voucher have been already used more times "
                            f"({current_usage_total}) than new limit.",
                            code=DiscountErrorCode.USAGE_LIMIT_EXCEEDED.value,
                        )
                    }
                )
            voucher_codes = instance.codes.all()
            for code in voucher_codes:
                code.used = current_usage_data.get(code.code, 0)

    @classmethod
    def construct_codes_instances(
        cls, code, codes_data, cleaned_input, voucher_instance
    ):
        if codes_data:
            return [
                models.VoucherCode(
                    code=code,
                    voucher=voucher_instance,
                )
                for code in codes_data
            ]

        if code:
            if voucher_instance.codes.count() == 1:
                code_instance = voucher_instance.codes.first()
                code_instance.code = code
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

        return []

    @classmethod
    def save(  # type: ignore[override]
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
            models.VoucherCode.objects.bulk_update(codes_to_update, fields=["code"])

    @classmethod
    def post_save_action(  # type: ignore[override]
        cls, info: ResolveInfo, instance, codes_instances, cleaned_input
    ):
        manager = get_plugin_manager_promise(info.context).get()

        if cleaned_input:
            cls.call_event(manager.voucher_updated, instance, instance.code)
        if codes_instances:
            cls.call_event(manager.voucher_codes_created, codes_instances)

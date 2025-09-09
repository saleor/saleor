import graphene
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Exists, OuterRef

from .....checkout import models as checkout_models
from .....discount import models
from .....discount.error_codes import DiscountErrorCode
from .....order import models as order_models
from .....permission.enums import DiscountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.types import DiscountError
from ....directives import doc, webhook_events
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Voucher
from .voucher_create import VoucherInput, VoucherMutationBase


@doc(category=DOC_CATEGORY_DISCOUNTS)
@webhook_events(
    async_events={
        WebhookEventAsyncType.VOUCHER_UPDATED,
        WebhookEventAsyncType.VOUCHER_CODES_CREATED,
    }
)
class VoucherUpdate(VoucherMutationBase):
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

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cls.clean_codes(data)
        cls.clean_voucher_usage_setting(instance, data)
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
        """Ensure voucher usage settings are not changed if voucher was already used."""
        is_voucher_used = None
        if "single_use" in data and instance.single_use != data["single_use"]:
            is_voucher_used = cls.is_voucher_used(instance)
            if is_voucher_used:
                raise ValidationError(
                    {
                        "single_use": ValidationError(
                            "Cannot change single use setting when any voucher code has "
                            "already been used.",
                            code=DiscountErrorCode.VOUCHER_ALREADY_USED.value,
                        )
                    }
                )
        if "usage_limit" in data and instance.usage_limit != data["usage_limit"]:
            if is_voucher_used is None:
                is_voucher_used = cls.is_voucher_used(instance)
            if is_voucher_used:
                raise ValidationError(
                    {
                        "usage_limit": ValidationError(
                            "Cannot change usage limit setting when any voucher code has "
                            "already been used.",
                            code=DiscountErrorCode.VOUCHER_ALREADY_USED.value,
                        )
                    }
                )

    @classmethod
    def is_voucher_used(cls, instance) -> bool:
        voucher_codes = instance.codes.all()
        used_codes = voucher_codes.filter(
            Exists(
                order_models.Order.objects.filter(
                    voucher_code=OuterRef("code"), voucher_id=OuterRef("voucher_id")
                )
            )
            | Exists(
                order_models.OrderLine.objects.filter(
                    voucher_code=OuterRef("code"),
                )
            )
            | Exists(
                checkout_models.Checkout.objects.filter(voucher_code=OuterRef("code"))
            )
        )
        return used_codes.exists()

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

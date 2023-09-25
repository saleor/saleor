import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from .....core.utils.promo_code import generate_promo_code, is_available_promo_code
from .....discount import models
from .....discount.error_codes import DiscountErrorCode
from .....permission.enums import DiscountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....channel import ChannelContext
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_31, ADDED_IN_318, DEPRECATED_IN_3X_FIELD
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.mutations import ModelMutation
from ....core.types import BaseInputObjectType, DiscountError, NonNullList
from ....core.utils import WebhookEventInfo, get_duplicated_values
from ....core.validators import (
    validate_end_is_after_start,
    validate_one_of_args_is_in_mutation,
)
from ....plugins.dataloaders import get_plugin_manager_promise
from ...enums import DiscountValueTypeEnum, VoucherTypeEnum
from ...types import Voucher


class VoucherCodeInput(BaseInputObjectType):
    code = graphene.String(description="Code to use the voucher.", required=False)
    usage_limit = graphene.Int(description="Code usage limit.", required=False)

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS
        description = "Represents voucher code data." + ADDED_IN_318


class VoucherInput(BaseInputObjectType):
    type = VoucherTypeEnum(
        description="Voucher type: PRODUCT, CATEGORY SHIPPING or ENTIRE_ORDER."
    )
    name = graphene.String(description="Voucher name.")
    code = graphene.String(
        required=False, description="Code to use the voucher." + DEPRECATED_IN_3X_FIELD
    )
    codes = NonNullList(
        VoucherCodeInput, description="Codes to use the voucher." + ADDED_IN_318
    )
    start_date = graphene.types.datetime.DateTime(
        description="Start date of the voucher in ISO 8601 format."
    )
    end_date = graphene.types.datetime.DateTime(
        description="End date of the voucher in ISO 8601 format."
    )
    discount_value_type = DiscountValueTypeEnum(
        description="Choices: fixed or percentage."
    )
    products = NonNullList(
        graphene.ID, description="Products discounted by the voucher.", name="products"
    )
    variants = NonNullList(
        graphene.ID,
        description="Variants discounted by the voucher." + ADDED_IN_31,
        name="variants",
    )
    collections = NonNullList(
        graphene.ID,
        description="Collections discounted by the voucher.",
        name="collections",
    )
    categories = NonNullList(
        graphene.ID,
        description="Categories discounted by the voucher.",
        name="categories",
    )
    min_checkout_items_quantity = graphene.Int(
        description="Minimal quantity of checkout items required to apply the voucher."
    )
    countries = NonNullList(
        graphene.String,
        description="Country codes that can be used with the shipping voucher.",
    )
    apply_once_per_order = graphene.Boolean(
        description="Voucher should be applied to the cheapest item or entire order."
    )
    apply_once_per_customer = graphene.Boolean(
        description="Voucher should be applied once per customer."
    )
    only_for_staff = graphene.Boolean(
        description="Voucher can be used only by staff user."
    )
    usage_limit = graphene.Int(
        description=(
            "Limit number of times this voucher can be used in total."
            + DEPRECATED_IN_3X_FIELD
        )
    )

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS


class VoucherCreate(ModelMutation):
    class Arguments:
        input = VoucherInput(
            required=True, description="Fields required to create a voucher."
        )

    class Meta:
        description = "Creates a new voucher."
        model = models.Voucher
        object_type = Voucher
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.VOUCHER_CREATED,
                description="A voucher was created.",
            )
        ]

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cls.clean_codes(data)
        cleaned_input = super().clean_input(info, instance, data, **kwargs)

        return cleaned_input

    @classmethod
    def _clean_old_code(cls, data):
        # Deprecated in 3.0, remove in 4.0
        data["code"] = data.code.strip() if data.code else None

        if not data["code"]:
            data["code"] = generate_promo_code()
        elif not is_available_promo_code(data["code"]):
            raise ValidationError(
                {
                    "code": ValidationError(
                        "Promo code already exists.",
                        code=DiscountErrorCode.ALREADY_EXISTS.value,
                    )
                }
            )

    @classmethod
    def _clean_new_codes(cls, data):
        codes = [code_data.code.strip() for code_data in data.codes if code_data.code]
        duplicated_codes = get_duplicated_values(codes)

        if duplicated_codes:
            raise ValidationError(
                {
                    "codes": ValidationError(
                        "Duplicated promo codes provided.",
                        code=DiscountErrorCode.DUPLICATED_INPUT_ITEM.value,
                        params={"voucher_codes": duplicated_codes},
                    )
                }
            )

        existing_codes = []
        for code_data in data.codes:
            code_data["code"] = code_data.code.strip() if code_data.code else None

            if not code_data["code"]:
                code_data["code"] = generate_promo_code()
            elif not is_available_promo_code(code_data["code"]):
                existing_codes.append(code_data["code"])

        if existing_codes:
            raise ValidationError(
                {
                    "codes": ValidationError(
                        "Promo code already exists.",
                        code=DiscountErrorCode.ALREADY_EXISTS.value,
                        params={"voucher_codes": existing_codes},
                    )
                }
            )

    @classmethod
    def clean_codes(cls, data):
        if data.code != "":
            validate_one_of_args_is_in_mutation(
                "code",
                data.code,
                "codes",
                data.codes,
                use_camel_case=True,
            )

        if "code" in data:
            cls._clean_old_code(data)
        else:
            cls._clean_new_codes(data)

    @classmethod
    def construct_codes_instances(
        cls, code, codes_data, cleaned_input, voucher_instance
    ):
        if code:
            return [
                models.VoucherCode(
                    code=code,
                    usage_limit=cleaned_input.get("usage_limit"),
                    voucher=voucher_instance,
                )
            ]
        else:
            return [
                models.VoucherCode(
                    code=code_data["code"],
                    usage_limit=code_data.get("usage_limit"),
                    voucher=voucher_instance,
                )
                for code_data in codes_data
            ]

    @classmethod
    def clean_voucher_instance(cls, info: ResolveInfo, voucher_instance):
        cls.clean_instance(info, voucher_instance)

        start_date = voucher_instance.start_date
        end_date = voucher_instance.end_date

        try:
            validate_end_is_after_start(start_date, end_date)
        except ValidationError as error:
            error.code = DiscountErrorCode.INVALID.value
            raise ValidationError({"end_date": error})

    @classmethod
    def clean_codes_instance(cls, code_instances):
        for code_instance in code_instances:
            code_instance.full_clean(exclude=["voucher"])

    @classmethod
    def save(  # type: ignore[override]
        cls, _info: ResolveInfo, voucher_instance, code_instances, has_multiple_codes
    ):
        with transaction.atomic():
            voucher_instance.save()
            models.VoucherCode.objects.bulk_create(code_instances)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, code):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.voucher_created, instance, code)

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        voucher_instance = cls.get_instance(info, **data)
        data = data.get("input")
        cleaned_input = cls.clean_input(info, voucher_instance, data)

        metadata_list = cleaned_input.pop("metadata", None)
        private_metadata_list = cleaned_input.pop("private_metadata", None)
        codes_data = cleaned_input.pop("codes", None)
        code = cleaned_input.pop("code", None)

        voucher_instance = cls.construct_instance(voucher_instance, cleaned_input)
        code_instances = cls.construct_codes_instances(
            code, codes_data, cleaned_input, voucher_instance
        )

        cls.validate_and_update_metadata(
            voucher_instance, metadata_list, private_metadata_list
        )

        cls.clean_voucher_instance(info, voucher_instance)
        cls.clean_codes_instance(code_instances)

        has_multiple_codes = bool(codes_data)
        cls.save(info, voucher_instance, code_instances, has_multiple_codes)

        cls.post_save_action(info, voucher_instance, code_instances[0].code)
        return cls.success_response(voucher_instance)

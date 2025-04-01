import graphene
from django.core.exceptions import ValidationError

from ....account.models import User
from ....checkout import AddressType
from ....core.tracing import traced_atomic_transaction
from ....discount.models import VoucherCode
from ....discount.utils.voucher import (
    create_or_update_voucher_discount_objects_for_order,
    increase_voucher_usage,
    release_voucher_code_usage,
)
from ....order import OrderStatus, models
from ....order.actions import call_order_event
from ....order.error_codes import OrderErrorCode
from ....order.search import update_order_search_vector
from ....order.utils import (
    invalidate_order_prices,
    update_order_display_gross_prices,
)
from ....permission.enums import OrderPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...account.i18n import I18nMixin
from ...account.mixins import AddressMetadataMixin
from ...core import ResolveInfo
from ...core.context import SyncWebhookControlContext
from ...core.mutations import (
    ModelWithExtRefMutation,
    ModelWithRestrictedChannelAccessMutation,
)
from ...core.types import OrderError
from ...meta.inputs import MetadataInput
from ...plugins.dataloaders import get_plugin_manager_promise
from ...shipping.utils import get_shipping_model_by_object_id
from ..types import Order
from . import draft_order_cleaner
from .draft_order_create import DraftOrderInput
from .utils import (
    SHIPPING_METHOD_UPDATE_FIELDS,
    ShippingMethodUpdateMixin,
    save_addresses,
)


class DraftOrderUpdate(
    AddressMetadataMixin,
    ModelWithRestrictedChannelAccessMutation,
    ModelWithExtRefMutation,
    I18nMixin,
):
    class Arguments:
        id = graphene.ID(required=False, description="ID of a draft order to update.")
        external_reference = graphene.String(
            required=False,
            description="External ID of a draft order to update.",
        )
        input = DraftOrderInput(
            required=True, description="Fields required to update an order."
        )

    class Meta:
        description = "Updates a draft order."
        model = models.Order
        object_type = Order
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"
        support_meta_field = True
        support_private_meta_field = True

    @classmethod
    def get_instance(cls, info: ResolveInfo, **data):
        instance = super().get_instance(
            info, qs=models.Order.objects.prefetch_related("lines"), **data
        )
        if instance.status != OrderStatus.DRAFT:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Provided order id belongs to non-draft order. "
                        "Use `orderUpdate` mutation instead.",
                        code=OrderErrorCode.INVALID.value,
                    )
                }
            )
        return instance

    @classmethod
    def should_invalidate_prices(cls, cleaned_input, *args) -> bool:
        return any(
            field in cleaned_input
            for field in [
                "shipping_address",
                "billing_address",
                "shipping_method",
                "voucher",
            ]
        )

    @classmethod
    def clean_input(
        cls, info: ResolveInfo, instance: models.Order, data: dict, **kwargs
    ):
        cls.clean_channel_id(instance, data)
        manager = get_plugin_manager_promise(info.context).get()
        shipping_address = data.pop("shipping_address", None)
        billing_address = data.pop("billing_address", None)
        redirect_url = data.pop("redirect_url", None)

        shipping_method_input = {}
        if "shipping_method" in data:
            shipping_method_input["shipping_method"] = get_shipping_model_by_object_id(
                object_id=data.pop("shipping_method", None),
                error_field="shipping_method",
            )

        if email := data.get("user_email", None):
            try:
                user = User.objects.get(email=email, is_active=True)
                data["user"] = graphene.Node.to_global_id("User", user.id)
            except User.DoesNotExist:
                data["user"] = None

        cleaned_input = super().clean_input(info, instance, data, **kwargs)

        cleaned_input.update(shipping_method_input)

        channel = instance.channel or cleaned_input.get("channel_id")
        draft_order_cleaner.clean_voucher_and_voucher_code(channel, cleaned_input)

        cls.clean_addresses(
            info, instance, cleaned_input, shipping_address, billing_address, manager
        )

        draft_order_cleaner.clean_redirect_url(redirect_url, cleaned_input)

        return cleaned_input

    @classmethod
    def clean_channel_id(cls, instance, data):
        if data.get("channel_id"):
            if hasattr(instance, "channel"):
                raise ValidationError(
                    {
                        "channel_id": ValidationError(
                            "Can't update existing order channel id.",
                            code=OrderErrorCode.NOT_EDITABLE.value,
                        )
                    }
                )

    @classmethod
    def clean_addresses(
        cls,
        info: ResolveInfo,
        instance,
        cleaned_input,
        shipping_address,
        billing_address,
        manager,
    ):
        save_shipping_address = cleaned_input.get("save_shipping_address")
        save_billing_address = cleaned_input.get("save_billing_address")
        if shipping_address:
            shipping_address = cls.validate_address(
                shipping_address,
                address_type=AddressType.SHIPPING,
                instance=instance.shipping_address,
                info=info,
            )
            cleaned_input["shipping_address"] = shipping_address
            cleaned_input["draft_save_shipping_address"] = (
                save_shipping_address or False
            )
        elif save_shipping_address is not None:
            raise ValidationError(
                {
                    "save_shipping_address": ValidationError(
                        "This option can only be selected if a shipping address "
                        "is provided.",
                        code=OrderErrorCode.MISSING_ADDRESS_DATA.value,
                    )
                }
            )
        if billing_address:
            billing_address = cls.validate_address(
                billing_address,
                address_type=AddressType.BILLING,
                instance=instance.billing_address,
                info=info,
            )
            cleaned_input["billing_address"] = billing_address
            cleaned_input["draft_save_billing_address"] = save_billing_address or False
        elif save_billing_address is not None:
            raise ValidationError(
                {
                    "save_billing_address": ValidationError(
                        "This option can only be selected if a billing address "
                        "is provided.",
                        code=OrderErrorCode.MISSING_ADDRESS_DATA.value,
                    )
                }
            )

    @classmethod
    def _save(
        cls,
        info: ResolveInfo,
        instance,
        cleaned_input,
        old_voucher,
        old_voucher_code,
        changed_fields,
    ):
        updated_fields = changed_fields
        manager = get_plugin_manager_promise(info.context).get()
        with traced_atomic_transaction():
            # Process addresses
            address_fields = save_addresses(instance, cleaned_input)
            updated_fields.extend(address_fields)

            if "shipping_method" in cleaned_input:
                method = cleaned_input["shipping_method"]
                if method is None:
                    ShippingMethodUpdateMixin.clear_shipping_method_from_order(instance)
                else:
                    ShippingMethodUpdateMixin.process_shipping_method(
                        instance, method, manager, update_shipping_discount=True
                    )
                updated_fields.extend(SHIPPING_METHOD_UPDATE_FIELDS)

            if instance.undiscounted_base_shipping_price_amount is None:
                instance.undiscounted_base_shipping_price_amount = (
                    instance.base_shipping_price_amount
                )
                updated_fields.append("undiscounted_base_shipping_price_amount")

            if "voucher" in cleaned_input:
                cls.handle_order_voucher(
                    cleaned_input,
                    instance,
                    old_voucher,
                    old_voucher_code,
                )

            # In case nothing change, do not update perform post-process actions;
            # do not call the `DRAFT_ORDER_UPDATED` event.
            if not updated_fields:
                return

            if (
                "shipping_address" in updated_fields
                or "billing_address" in updated_fields
            ):
                update_order_display_gross_prices(instance)
                updated_fields.append("display_gross_prices")

            update_order_search_vector(instance, save=False)
            # Post-process the results
            updated_fields.extend(
                [
                    "search_vector",
                    "updated_at",
                ]
            )

            if cls.should_invalidate_prices(cleaned_input):
                invalidate_order_prices(instance)
                updated_fields.extend(["should_refresh_prices"])

            instance.save(update_fields=updated_fields)

            call_order_event(
                manager,
                WebhookEventAsyncType.DRAFT_ORDER_UPDATED,
                instance,
            )

    @classmethod
    def handle_order_voucher(
        cls,
        cleaned_input,
        instance: models.Order,
        old_voucher,
        old_voucher_code,
    ):
        voucher = cleaned_input["voucher"]
        if voucher is None and old_voucher is None:
            return

        # create or update voucher discount object
        create_or_update_voucher_discount_objects_for_order(instance)

        # handle voucher usage
        user_email = instance.user_email
        if not user_email and instance.user:
            user_email = instance.user.email

        channel = instance.channel
        if not channel.include_draft_order_in_voucher_usage:
            return

        if voucher:
            code_instance = cleaned_input.pop("voucher_code_instance", None)
            increase_voucher_usage(
                voucher,
                code_instance,
                user_email,
                increase_voucher_customer_usage=False,
            )
        elif old_voucher:
            # handle removing voucher
            voucher_code = VoucherCode.objects.filter(code=old_voucher_code).first()
            release_voucher_code_usage(voucher_code, old_voucher, user_email)

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        instance = cls.get_instance(info, **data)
        channel_id = cls.get_instance_channel_id(instance, **data)

        cls.check_channel_permissions(info, [channel_id])

        old_instance_data = instance.serialize_for_comparison()
        old_voucher = instance.voucher
        old_voucher_code = instance.voucher_code
        data = data["input"]
        cleaned_input = cls.clean_input(info, instance, data)
        metadata_list: list[MetadataInput] = cleaned_input.pop("metadata", None)
        private_metadata_list: list[MetadataInput] = cleaned_input.pop(
            "private_metadata", None
        )

        metadata_collection = cls.create_metadata_from_graphql_input(
            metadata_list, error_field_name="metadata"
        )
        private_metadata_collection = cls.create_metadata_from_graphql_input(
            private_metadata_list, error_field_name="private_metadata"
        )

        instance = cls.construct_instance(instance, cleaned_input)

        cls.validate_and_update_metadata(
            instance, metadata_collection, private_metadata_collection
        )
        cls.clean_instance(info, instance)
        new_instance_data = instance.serialize_for_comparison()
        changed_fields = cls.diff_instance_data_fields(
            instance.comparison_fields,
            old_instance_data,
            new_instance_data,
        )
        cls._save(
            info, instance, cleaned_input, old_voucher, old_voucher_code, changed_fields
        )
        cls._save_m2m(info, instance, cleaned_input)

        return DraftOrderUpdate(order=SyncWebhookControlContext(node=instance))

    @classmethod
    def get_instance_channel_id(cls, instance, **data):
        if channel_id := instance.channel_id:
            return channel_id
        return None

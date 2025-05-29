from typing import cast

import graphene
from django.core.exceptions import ValidationError

from ....account.models import User
from ....checkout import AddressType
from ....core.tracing import traced_atomic_transaction
from ....core.utils.update_mutation_manager import InstanceTracker
from ....discount.models import VoucherCode
from ....discount.utils.voucher import (
    create_or_update_voucher_discount_objects_for_order,
    get_customer_email_for_voucher_usage,
    increase_voucher_usage,
    release_voucher_code_usage,
)
from ....order import OrderStatus, models
from ....order.actions import call_order_event
from ....order.error_codes import OrderErrorCode
from ....order.search import update_order_search_vector
from ....order.utils import invalidate_order_prices
from ....permission.enums import OrderPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...account.i18n import I18nMixin
from ...account.mixins import AddressMetadataMixin
from ...account.mutations.account.utils import ADDRESS_UPDATE_FIELDS
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
    DRAFT_ORDER_UPDATE_FIELDS,
    SHIPPING_METHOD_UPDATE_FIELDS,
    ShippingMethodUpdateMixin,
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

    FIELDS_TO_TRACK = list(DRAFT_ORDER_UPDATE_FIELDS | SHIPPING_METHOD_UPDATE_FIELDS)

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
                "voucher_code",
            ]
        )

    @classmethod
    def clean_input(
        cls, info: ResolveInfo, instance: models.Order, data: dict, **kwargs
    ):
        cls.clean_channel_id(instance, data)
        shipping_address = data.pop("shipping_address", None)
        billing_address = data.pop("billing_address", None)
        redirect_url = data.pop("redirect_url", "")

        shipping_method_input = cls.clean_shipping_method(instance, data)

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
            info, instance, cleaned_input, shipping_address, billing_address
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
    def clean_shipping_method(cls, instance, cleaned_input):
        shipping_method_input = {}
        if "shipping_method" in cleaned_input:
            shipping_method = get_shipping_model_by_object_id(
                object_id=cleaned_input.pop("shipping_method", None),
                error_field="shipping_method",
            )
            shipping_method_input["shipping_method"] = shipping_method

            # Do not process shipping method if it is already associated with the order
            # and shipping price is properly set. Shipping price can be not set together
            # with shipping method when it is added to the order without lines or with
            # lines that do not require shipping.
            if shipping_method is not None:
                method_channel_listing = shipping_method.channel_listings.filter(
                    channel=instance.channel
                ).first()
                shipping_price = (
                    method_channel_listing.price if method_channel_listing else 0
                )
                shipping_price_update_required = (
                    shipping_method.id == instance.shipping_method_id
                    and instance.undiscounted_base_shipping_price != shipping_price
                )
                shipping_method_update_required = (
                    shipping_method.id != instance.shipping_method_id
                )
                shipping_update_required = (
                    shipping_method_update_required or shipping_price_update_required
                )
                if not shipping_update_required:
                    shipping_method_input = {}

        return shipping_method_input

    @classmethod
    def clean_addresses(
        cls,
        info: ResolveInfo,
        instance,
        cleaned_input,
        shipping_address,
        billing_address,
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
            instance.shipping_address = shipping_address
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
            instance.billing_address = billing_address
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
        instance_tracker: InstanceTracker,
        cleaned_input: dict,
    ) -> bool:
        instance = cast(models.Order, instance_tracker.instance)
        with traced_atomic_transaction():
            modified_foreign_fields = instance_tracker.get_foreign_modified_fields()
            if "shipping_address" in modified_foreign_fields:
                cls._save_address(
                    instance.shipping_address,
                    modified_foreign_fields["shipping_address"],
                )

            if "billing_address" in modified_foreign_fields:
                cls._save_address(
                    instance.billing_address,
                    modified_foreign_fields["billing_address"],
                )

            modified_instance_fields = instance_tracker.get_modified_fields()
            modified_instance_fields.extend(modified_foreign_fields)
            if not modified_instance_fields:
                return False

            # Post-process the results
            update_order_search_vector(instance, save=False)
            modified_instance_fields.extend(["search_vector"])
            if cls.should_invalidate_prices(modified_instance_fields):
                invalidate_order_prices(instance)
                modified_instance_fields.extend(["should_refresh_prices"])

            # Save instance
            cls._save_order_instance(instance, modified_instance_fields)

            return True

    @classmethod
    def _save_order_instance(cls, instance, modified_instance_fields):
        update_fields = ["updated_at"] + modified_instance_fields
        instance.save(update_fields=update_fields)

    @classmethod
    def _save_address(cls, address_instance, modified_fields):
        if address_instance._state.adding:
            address_instance.save()
        else:
            address_instance.save(update_fields=modified_fields)

    @classmethod
    def _post_save_action(cls, instance, manager):
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
        if "voucher" not in cleaned_input:
            return

        voucher = cleaned_input["voucher"]
        if voucher is None and old_voucher is None:
            return

        # create or update voucher discount object
        create_or_update_voucher_discount_objects_for_order(instance)

        # handle voucher usage
        user_email = get_customer_email_for_voucher_usage(instance)

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
            # user_email is None as we do not have anything to release in terms of
            # apply once per customer
            release_voucher_code_usage(voucher_code, old_voucher, user_email=None)

    @classmethod
    def handle_shipping(cls, cleaned_input, instance: models.Order, manager):
        if "shipping_method" not in cleaned_input:
            return

        method = cleaned_input["shipping_method"]
        if method is None:
            ShippingMethodUpdateMixin.clear_shipping_method_from_order(instance)
        else:
            ShippingMethodUpdateMixin.process_shipping_method(
                instance, method, manager, update_shipping_discount=True
            )

    @classmethod
    def handle_metadata(cls, instance: models.Order, cleaned_input):
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
        cls.validate_and_update_metadata(
            instance, metadata_collection, private_metadata_collection
        )

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        instance = cls.get_instance(info, **data)
        channel_id = instance.channel_id
        cls.check_channel_permissions(info, [channel_id])

        instance = cast(models.Order, instance)
        instance_tracker = InstanceTracker(
            instance,
            cls.FIELDS_TO_TRACK,
            foreign_fields_to_track={
                "shipping_address": list(ADDRESS_UPDATE_FIELDS),
                "billing_address": list(ADDRESS_UPDATE_FIELDS),
            },
        )

        old_voucher = instance.voucher
        old_voucher_code = instance.voucher_code
        data = data["input"]
        cleaned_input = cls.clean_input(info, instance, data)

        cls.handle_metadata(instance, cleaned_input)

        # update instance with data from input
        instance = cls.construct_instance(instance, cleaned_input)

        cls.clean_instance(info, instance)

        manager = get_plugin_manager_promise(info.context).get()
        cls.handle_shipping(cleaned_input, instance, manager)
        cls.handle_order_voucher(cleaned_input, instance, old_voucher, old_voucher_code)

        order_modified = cls._save(instance_tracker, cleaned_input)
        if order_modified:
            cls._post_save_action(instance, manager)

        return DraftOrderUpdate(order=SyncWebhookControlContext(node=instance))

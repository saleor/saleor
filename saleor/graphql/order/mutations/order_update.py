from uuid import UUID

import graphene
from django.core.exceptions import ValidationError

from ....account.models import User
from ....checkout import AddressType
from ....core.postgres import FlatConcatSearchVector
from ....core.tracing import traced_atomic_transaction
from ....order import OrderStatus, models
from ....order.actions import call_order_event
from ....order.error_codes import OrderErrorCode
from ....order.search import prepare_order_search_vector_value
from ....order.utils import invalidate_order_prices
from ....permission.enums import OrderPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...account.i18n import I18nMixin
from ...account.mixins import AddressMetadataMixin
from ...account.types import AddressInput
from ...core import ResolveInfo
from ...core.context import SyncWebhookControlContext
from ...core.descriptions import ADDED_IN_321
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.enums import LanguageCodeEnum
from ...core.mutations import ModelWithExtRefMutation
from ...core.types import BaseInputObjectType, NonNullList, OrderError
from ...meta.inputs import MetadataInput, MetadataInputDescription
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Order
from .utils import save_addresses


class OrderUpdateInput(BaseInputObjectType):
    billing_address = AddressInput(description="Billing address of the customer.")
    user_email = graphene.String(description="Email address of the customer.")
    shipping_address = AddressInput(description="Shipping address of the customer.")
    external_reference = graphene.String(
        description="External ID of this order.", required=False
    )
    metadata = NonNullList(
        MetadataInput,
        description=(
            f"Order public metadata. {ADDED_IN_321}"
            f"{MetadataInputDescription.PUBLIC_METADATA_INPUT}"
        ),
        required=False,
    )

    private_metadata = NonNullList(
        MetadataInput,
        description=(
            f"Order private metadata. {ADDED_IN_321}"
            f"{MetadataInputDescription.PRIVATE_METADATA_INPUT}"
        ),
        required=False,
    )

    language_code = graphene.Argument(
        LanguageCodeEnum,
        required=False,
        description=(f"Order language code.{ADDED_IN_321}"),
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderUpdate(AddressMetadataMixin, ModelWithExtRefMutation, I18nMixin):
    class Arguments:
        id = graphene.ID(required=False, description="ID of an order to update.")
        external_reference = graphene.String(
            required=False,
            description="External ID of an order to update.",
        )
        input = OrderUpdateInput(
            required=True, description="Fields required to update an order."
        )

    class Meta:
        description = "Updates an order."
        model = models.Order
        object_type = Order
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"
        support_meta_field = True
        support_private_meta_field = True

    @classmethod
    def get_instance(cls, info: ResolveInfo, **data):
        instance = super().get_instance(info, **data)
        if instance.status == OrderStatus.DRAFT:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Provided order id belongs to draft order. "
                        "Use `draftOrderUpdate` mutation instead.",
                        code=OrderErrorCode.INVALID.value,
                    )
                }
            )
        return instance

    @classmethod
    def should_invalidate_prices(cls, cleaned_input, *args) -> bool:
        return any(
            cleaned_input.get(field) is not None
            for field in ["shipping_address", "billing_address"]
        )

    @classmethod
    def _save(cls, info: ResolveInfo, instance, cleaned_input, changed_fields):
        update_fields = changed_fields
        with traced_atomic_transaction():
            address_fields = save_addresses(instance, cleaned_input)
            update_fields.extend(address_fields)

            manager = get_plugin_manager_promise(info.context).get()
            if cls.should_invalidate_prices(cleaned_input):
                invalidate_order_prices(instance)
                update_fields.append("should_refresh_prices")

            if update_fields:
                instance.search_vector = FlatConcatSearchVector(
                    *prepare_order_search_vector_value(instance)
                )
                update_fields.extend(["updated_at", "search_vector"])

                instance.save(update_fields=update_fields)
                call_order_event(
                    manager,
                    WebhookEventAsyncType.ORDER_UPDATED,
                    instance,
                )

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        shipping_address_data = data.pop("shipping_address", None)
        billing_address_data = data.pop("billing_address", None)
        cleaned_input = super().clean_input(info, instance, data, **kwargs)

        if email := cleaned_input.get("user_email", None):
            if email == instance.user_email:
                cleaned_input.pop("user_email")
            try:
                user = User.objects.get(email=email, is_active=True)
                if user.id != instance.user_id:
                    cleaned_input["user"] = user
            except User.DoesNotExist:
                if instance.user_id:
                    cleaned_input["user"] = None

        if shipping_address_data:
            cleaned_input["shipping_address"] = cls.validate_address(
                shipping_address_data,
                address_type=AddressType.SHIPPING,
                info=info,
            )

        if billing_address_data:
            cleaned_input["billing_address"] = cls.validate_address(
                billing_address_data,
                address_type=AddressType.BILLING,
                info=info,
            )

        return cleaned_input

    @classmethod
    def get_instance_channel_id(cls, instance, **data) -> UUID | int:
        return instance.channel_id

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        instance = cls.get_instance(info, **data)
        channel_id = cls.get_instance_channel_id(instance, **data)
        cls.check_channel_permissions(info, [channel_id])
        old_instance_data = instance.serialize_for_comparison()
        data = data.get("input")
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
        cls._save(info, instance, cleaned_input, changed_fields)
        return OrderUpdate(order=SyncWebhookControlContext(instance))

from typing import Union
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
from ...core.descriptions import ADDED_IN_310
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import ModelWithExtRefMutation
from ...core.types import BaseInputObjectType, OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Order
from .utils import save_addresses


class OrderUpdateInput(BaseInputObjectType):
    billing_address = AddressInput(description="Billing address of the customer.")
    user_email = graphene.String(description="Email address of the customer.")
    shipping_address = AddressInput(description="Shipping address of the customer.")
    external_reference = graphene.String(
        description="External ID of this order." + ADDED_IN_310, required=False
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderUpdate(AddressMetadataMixin, ModelWithExtRefMutation, I18nMixin):
    class Arguments:
        id = graphene.ID(required=False, description="ID of an order to update.")
        external_reference = graphene.String(
            required=False,
            description=f"External ID of an order to update. {ADDED_IN_310}",
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
    def save(cls, info: ResolveInfo, instance, cleaned_input):
        update_fields = list(cleaned_input.keys())
        with traced_atomic_transaction():
            save_addresses(instance, cleaned_input)

            manager = get_plugin_manager_promise(info.context).get()
            if cls.should_invalidate_prices(cleaned_input):
                invalidate_order_prices(instance)
                update_fields.append("should_refresh_prices")

            if update_fields:
                instance.search_vector = FlatConcatSearchVector(
                    *prepare_order_search_vector_value(instance)
                )
                update_fields.extend(["updated_at", "search_vector"])

            if update_fields:
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
    def get_instance_channel_id(cls, instance, **data) -> Union[UUID, int]:
        return instance.channel_id

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        instance = cls.get_instance(info, **data)
        channel_id = cls.get_instance_channel_id(instance, **data)
        cls.check_channel_permissions(info, [channel_id])
        data = data.get("input")
        cleaned_input = cls.clean_input(info, instance, data)
        instance = cls.construct_instance(instance, cleaned_input)

        cls.clean_instance(info, instance)
        cls.save(info, instance, cleaned_input)
        return cls.success_response(instance)

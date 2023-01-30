import graphene
from django.core.exceptions import ValidationError

from ....account.models import User
from ....core.postgres import FlatConcatSearchVector
from ....core.tracing import traced_atomic_transaction
from ....order import OrderStatus, models
from ....order.error_codes import OrderErrorCode
from ....order.search import prepare_order_search_vector_value
from ....order.utils import invalidate_order_prices
from ....permission.enums import OrderPermissions
from ...account.types import AddressInput
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_310
from ...core.mutations import ModelWithExtRefMutation
from ...core.types import OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Order
from .draft_order_create import DraftOrderCreate


class OrderUpdateInput(graphene.InputObjectType):
    billing_address = AddressInput(description="Billing address of the customer.")
    user_email = graphene.String(description="Email address of the customer.")
    shipping_address = AddressInput(description="Shipping address of the customer.")
    external_reference = graphene.String(
        description="External ID of this order." + ADDED_IN_310, required=False
    )


class OrderUpdate(DraftOrderCreate, ModelWithExtRefMutation):
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
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        draft_order_cleaned_input = super().clean_input(info, instance, data, **kwargs)

        # We must to filter out field added by DraftOrderUpdate
        editable_fields = [
            "billing_address",
            "shipping_address",
            "user_email",
            "external_reference",
        ]
        cleaned_input = {}
        for key in draft_order_cleaned_input:
            if key in editable_fields:
                cleaned_input[key] = draft_order_cleaned_input[key]
        return cleaned_input

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
    def should_invalidate_prices(cls, instance, cleaned_input, is_new_instance) -> bool:
        return any(
            cleaned_input.get(field) is not None
            for field in ["shipping_address", "billing_address"]
        )

    @classmethod
    def save(cls, info: ResolveInfo, instance, cleaned_input):
        with traced_atomic_transaction():
            cls._save_addresses(instance, cleaned_input)
            if instance.user_email:
                user = User.objects.filter(email=instance.user_email).first()
                instance.user = user
            instance.search_vector = FlatConcatSearchVector(
                *prepare_order_search_vector_value(instance)
            )
            manager = get_plugin_manager_promise(info.context).get()
            if cls.should_invalidate_prices(instance, cleaned_input, False):
                invalidate_order_prices(instance)

            instance.save()
            cls.call_event(manager.order_updated, instance)

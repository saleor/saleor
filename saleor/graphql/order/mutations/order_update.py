import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ....account.models import User
from ....core.permissions import OrderPermissions
from ....core.postgres import FlatConcatSearchVector
from ....core.tracing import traced_atomic_transaction
from ....order import OrderStatus, models
from ....order.error_codes import OrderErrorCode
from ....order.search import prepare_order_search_vector_value
from ....order.utils import invalidate_order_prices
from ...account.types import AddressInput
from ...core.types import OrderError
from ..types import Order
from .draft_order_create import DraftOrderCreate


class OrderUpdateInput(graphene.InputObjectType):
    billing_address = AddressInput(description="Billing address of the customer.")
    user_email = graphene.String(description="Email address of the customer.")
    shipping_address = AddressInput(description="Shipping address of the customer.")


class OrderUpdate(DraftOrderCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of an order to update.")
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
    def clean_input(cls, info, instance, data):
        draft_order_cleaned_input = super().clean_input(info, instance, data)

        # We must to filter out field added by DraftOrderUpdate
        editable_fields = ["billing_address", "shipping_address", "user_email"]
        cleaned_input = {}
        for key in draft_order_cleaned_input:
            if key in editable_fields:
                cleaned_input[key] = draft_order_cleaned_input[key]
        return cleaned_input

    @classmethod
    def get_instance(cls, info, **data):
        instance = super().get_instance(info, **data)
        if instance.status == OrderStatus.DRAFT:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Provided order id belongs to draft order. "
                        "Use `draftOrderUpdate` mutation instead.",
                        code=OrderErrorCode.INVALID,
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
    @traced_atomic_transaction()
    def save(cls, info, instance, cleaned_input):
        cls._save_addresses(info, instance, cleaned_input)
        if instance.user_email:
            user = User.objects.filter(email=instance.user_email).first()
            instance.user = user
        instance.search_vector = FlatConcatSearchVector(
            *prepare_order_search_vector_value(instance)
        )

        if cls.should_invalidate_prices(instance, cleaned_input, False):
            invalidate_order_prices(instance)

        instance.save()
        transaction.on_commit(lambda: info.context.plugins.order_updated(instance))

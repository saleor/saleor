import graphene

from ....checkout import AddressType
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.utils import change_billing_address_in_checkout
from ....core.tracing import traced_atomic_transaction
from ...account.types import AddressInput
from ...core.descriptions import DEPRECATED_IN_3X_INPUT
from ...core.scalars import UUID
from ...core.types import CheckoutError
from ...core.validators import validate_one_of_args_is_in_mutation
from ..types import Checkout
from .checkout_shipping_address_update import CheckoutShippingAddressUpdate
from .utils import get_checkout_by_token


class CheckoutBillingAddressUpdate(CheckoutShippingAddressUpdate):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(
            required=False,
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} "
                "Use token instead."
            ),
        )
        token = UUID(description="Checkout token.", required=False)
        billing_address = AddressInput(
            required=True, description="The billing address of the checkout."
        )

    class Meta:
        description = "Update billing address in the existing checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(
        cls, _root, info, billing_address, checkout_id=None, token=None
    ):
        # DEPRECATED
        validate_one_of_args_is_in_mutation(
            CheckoutErrorCode, "checkout_id", checkout_id, "token", token
        )

        if token:
            checkout = get_checkout_by_token(token)
        # DEPRECATED
        else:
            checkout = cls.get_node_or_error(
                info, checkout_id or token, only_type=Checkout, field="checkout_id"
            )

        billing_address = cls.validate_address(
            billing_address,
            address_type=AddressType.BILLING,
            instance=checkout.billing_address,
            info=info,
        )
        with traced_atomic_transaction():
            billing_address.save()
            change_billing_address_in_checkout(checkout, billing_address)
            info.context.plugins.checkout_updated(checkout)
        return CheckoutBillingAddressUpdate(checkout=checkout)

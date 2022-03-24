import graphene

from ....checkout import AddressType
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.utils import (
    change_billing_address_in_checkout,
    invalidate_checkout_prices,
)
from ....core.tracing import traced_atomic_transaction
from ...account.types import AddressInput
from ...core.descriptions import DEPRECATED_IN_3X_INPUT
from ...core.scalars import UUID
from ...core.types.common import CheckoutError
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
            change_address_updated_fields = change_billing_address_in_checkout(
                checkout, billing_address
            )
            lines, _ = fetch_checkout_lines(checkout)
            checkout_info = fetch_checkout_info(
                checkout, lines, info.context.discounts, info.context.plugins
            )
            invalidate_prices_updated_fields = invalidate_checkout_prices(
                checkout_info,
                lines,
                info.context.plugins,
                info.context.discounts,
                save=False,
            )
            checkout.save(
                update_fields=change_address_updated_fields
                + invalidate_prices_updated_fields
            )

            info.context.plugins.checkout_updated(checkout)

        return CheckoutBillingAddressUpdate(checkout=checkout)

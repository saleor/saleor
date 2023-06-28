import graphene

from ....checkout import AddressType
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.utils import (
    change_billing_address_in_checkout,
    invalidate_checkout_prices,
)
from ....core.tracing import traced_atomic_transaction
from ....webhook.event_types import WebhookEventAsyncType
from ...account.types import AddressInput
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_34, ADDED_IN_35, DEPRECATED_IN_3X_INPUT
from ...core.doc_category import DOC_CATEGORY_CHECKOUT
from ...core.scalars import UUID
from ...core.types import CheckoutError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Checkout
from .checkout_create import CheckoutAddressValidationRules
from .checkout_shipping_address_update import CheckoutShippingAddressUpdate
from .utils import get_checkout


class CheckoutBillingAddressUpdate(CheckoutShippingAddressUpdate):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        id = graphene.ID(
            description="The checkout's ID." + ADDED_IN_34,
            required=False,
        )
        token = UUID(
            description=f"Checkout token.{DEPRECATED_IN_3X_INPUT} Use `id` instead.",
            required=False,
        )
        checkout_id = graphene.ID(
            required=False,
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} Use `id` instead."
            ),
        )
        billing_address = AddressInput(
            required=True, description="The billing address of the checkout."
        )
        validation_rules = CheckoutAddressValidationRules(
            required=False,
            description=(
                "The rules for changing validation for received billing address data."
                + ADDED_IN_35
            ),
        )

    class Meta:
        description = "Update billing address in the existing checkout."
        doc_category = DOC_CATEGORY_CHECKOUT
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CHECKOUT_UPDATED,
                description="A checkout was updated.",
            )
        ]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        billing_address,
        validation_rules=None,
        checkout_id=None,
        token=None,
        id=None,
    ):
        checkout = get_checkout(cls, info, checkout_id=checkout_id, token=token, id=id)

        address_validation_rules = validation_rules or {}
        billing_address = cls.validate_address(
            billing_address,
            address_type=AddressType.BILLING,
            instance=checkout.billing_address,
            info=info,
            format_check=address_validation_rules.get("check_fields_format", True),
            required_check=address_validation_rules.get("check_required_fields", True),
            enable_normalization=address_validation_rules.get(
                "enable_fields_normalization", True
            ),
        )
        manager = get_plugin_manager_promise(info.context).get()
        with traced_atomic_transaction():
            billing_address.save()
            change_address_updated_fields = change_billing_address_in_checkout(
                checkout, billing_address
            )
            lines, _ = fetch_checkout_lines(checkout)
            checkout_info = fetch_checkout_info(checkout, lines, manager)
            invalidate_prices_updated_fields = invalidate_checkout_prices(
                checkout_info,
                lines,
                manager,
                recalculate_discount=False,
                save=False,
            )
            checkout.save(
                update_fields=change_address_updated_fields
                + invalidate_prices_updated_fields
            )

            cls.call_event(manager.checkout_updated, checkout)

        return CheckoutBillingAddressUpdate(checkout=checkout)

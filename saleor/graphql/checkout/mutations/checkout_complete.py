from typing import TYPE_CHECKING, Iterable

import graphene
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError

from ....checkout import AddressType
from ....checkout.checkout_cleaner import validate_checkout_email
from ....checkout.complete_checkout import complete_checkout
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import (
    CheckoutLineInfo,
    fetch_checkout_info,
    fetch_checkout_lines,
)
from ....checkout.utils import is_shipping_required
from ....core import analytics
from ....core.permissions import AccountPermissions
from ....core.transactions import transaction_with_commit_on_errors
from ....order import models as order_models
from ...account.i18n import I18nMixin
from ...app.dataloaders import load_app
from ...core.descriptions import ADDED_IN_34, DEPRECATED_IN_3X_INPUT
from ...core.fields import JSONString
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError
from ...core.validators import validate_one_of_args_is_in_mutation
from ...discount.dataloaders import load_discounts
from ...order.types import Order
from ...site.dataloaders import load_site
from ...utils import get_user_or_app_from_context
from ..types import Checkout
from .utils import get_checkout

if TYPE_CHECKING:
    from ....account.models import Address


class CheckoutComplete(BaseMutation, I18nMixin):
    order = graphene.Field(Order, description="Placed order.")
    confirmation_needed = graphene.Boolean(
        required=True,
        default_value=False,
        description=(
            "Set to true if payment needs to be confirmed"
            " before checkout is complete."
        ),
    )
    confirmation_data = JSONString(
        required=False,
        description=(
            "Confirmation data used to process additional authorization steps."
        ),
    )

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
        store_source = graphene.Boolean(
            default_value=False,
            description=(
                "Determines whether to store the payment source for future usage. "
                f"{DEPRECATED_IN_3X_INPUT} Use checkoutPaymentCreate for this action."
            ),
        )
        redirect_url = graphene.String(
            required=False,
            description=(
                "URL of a view where users should be redirected to "
                "see the order details. URL in RFC 1808 format."
            ),
        )
        payment_data = JSONString(
            required=False,
            description=(
                "Client-side generated data required to finalize the payment."
            ),
        )

    class Meta:
        description = (
            "Completes the checkout. As a result a new order is created and "
            "a payment charge is made. This action requires a successful "
            "payment before it can be performed. "
            "In case additional confirmation step as 3D secure is required "
            "confirmationNeeded flag will be set to True and no order created "
            "until payment is confirmed with second call of this mutation."
        )
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def validate_checkout_addresses(
        cls,
        lines: Iterable[CheckoutLineInfo],
        shipping_address: "Address",
        billing_address: "Address",
    ):
        """Validate checkout addresses.

        Mutations for updating addresses have option to turn off a validation. To keep
        consistency, we need to validate it. This will confirm that we have a correct
        address and we can finalize a checkout. In case when address fields
        normalization was turned off, we apply it here.
        Raises ValidationError when any address is not correct.
        """
        if is_shipping_required(lines):
            if not shipping_address:
                raise ValidationError(
                    {
                        "shipping_address": ValidationError(
                            "Shipping address is not set",
                            code=CheckoutErrorCode.SHIPPING_ADDRESS_NOT_SET.value,
                        )
                    }
                )
            shipping_address_data = shipping_address.as_data()
            cls.validate_address(
                shipping_address_data,
                address_type=AddressType.SHIPPING,
                format_check=True,
                required_check=True,
                enable_normalization=True,
                instance=shipping_address,
            )
            if shipping_address_data != shipping_address.as_data():
                shipping_address.save()

        if not billing_address:
            raise ValidationError(
                {
                    "billing_address": ValidationError(
                        "Billing address is not set",
                        code=CheckoutErrorCode.BILLING_ADDRESS_NOT_SET.value,
                    )
                }
            )
        billing_address_data = billing_address.as_data()
        cls.validate_address(
            billing_address_data,
            address_type=AddressType.BILLING,
            format_check=True,
            required_check=True,
            enable_normalization=True,
            instance=billing_address,
        )
        if billing_address_data != billing_address.as_data():
            billing_address.save()

    @classmethod
    def perform_mutation(
        cls, _root, info, store_source, checkout_id=None, token=None, id=None, **data
    ):
        # DEPRECATED
        validate_one_of_args_is_in_mutation(
            CheckoutErrorCode, "checkout_id", checkout_id, "token", token, "id", id
        )

        tracking_code = analytics.get_client_id(info.context)
        with transaction_with_commit_on_errors():
            try:
                checkout = get_checkout(
                    cls,
                    info,
                    checkout_id=checkout_id,
                    token=token,
                    id=id,
                    error_class=CheckoutErrorCode,
                )
            except ValidationError as e:
                # DEPRECATED
                if id or checkout_id:
                    id = id or checkout_id
                    token = cls.get_global_id_or_error(
                        id, only_type=Checkout, field="id" if id else "checkout_id"
                    )

                order = order_models.Order.objects.get_by_checkout_token(token)
                if order:
                    if not order.channel.is_active:
                        raise ValidationError(
                            {
                                "channel": ValidationError(
                                    "Cannot complete checkout with inactive channel.",
                                    code=CheckoutErrorCode.CHANNEL_INACTIVE.value,
                                )
                            }
                        )
                    # The order is already created. We return it as a success
                    # checkoutComplete response. Order is anonymized for not logged in
                    # user
                    return CheckoutComplete(
                        order=order, confirmation_needed=False, confirmation_data={}
                    )
                raise e

            validate_checkout_email(checkout)

            manager = info.context.plugins
            lines, unavailable_variant_pks = fetch_checkout_lines(checkout)
            if unavailable_variant_pks:
                not_available_variants_ids = {
                    graphene.Node.to_global_id("ProductVariant", pk)
                    for pk in unavailable_variant_pks
                }
                raise ValidationError(
                    {
                        "lines": ValidationError(
                            "Some of the checkout lines variants are unavailable.",
                            code=CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.value,
                            params={"variants": not_available_variants_ids},
                        )
                    }
                )
            if not lines:
                raise ValidationError(
                    {
                        "lines": ValidationError(
                            "Cannot complete checkout without lines.",
                            code=CheckoutErrorCode.NO_LINES.value,
                        )
                    }
                )
            discounts = load_discounts(info.context)
            checkout_info = fetch_checkout_info(checkout, lines, discounts, manager)

            cls.validate_checkout_addresses(
                lines, checkout_info.shipping_address, checkout_info.billing_address
            )

            requestor = get_user_or_app_from_context(info.context)
            if requestor.has_perm(AccountPermissions.IMPERSONATE_USER):
                # Allow impersonating user and process a checkout by using user details
                # assigned to checkout.
                customer = checkout.user or AnonymousUser()
            else:
                customer = info.context.user

            site = load_site(info.context)
            order, action_required, action_data = complete_checkout(
                manager=manager,
                checkout_info=checkout_info,
                lines=lines,
                payment_data=data.get("payment_data", {}),
                store_source=store_source,
                discounts=discounts,
                user=customer,
                app=load_app(info.context),
                site_settings=site.settings,
                tracking_code=tracking_code,
                redirect_url=data.get("redirect_url"),
            )
        # If gateway returns information that additional steps are required we need
        # to inform the frontend and pass all required data
        return CheckoutComplete(
            order=order,
            confirmation_needed=action_required,
            confirmation_data=action_data,
        )

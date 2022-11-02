from datetime import timedelta
from typing import Iterable

import graphene
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from ....checkout import AddressType
from ....checkout.checkout_cleaner import (
    clean_checkout_shipping,
    validate_checkout_email,
)
from ....checkout.complete_checkout import (
    complete_checkout_post_payment_part,
    complete_checkout_pre_payment_part,
    process_payment,
)
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import (
    CheckoutInfo,
    CheckoutLineInfo,
    fetch_checkout_info,
    fetch_checkout_lines,
)
from ....checkout.utils import is_shipping_required
from ....core import analytics
from ....core.permissions import AccountPermissions
from ....core.transactions import transaction_with_commit_on_errors
from ....discount.utils import release_voucher_usage
from ....order import models as order_models
from ....payment import gateway
from ....warehouse.models import Reservation, Stock
from ...account.i18n import I18nMixin
from ...app.dataloaders import load_app
from ...core.descriptions import ADDED_IN_34, ADDED_IN_38, DEPRECATED_IN_3X_INPUT
from ...core.fields import JSONString
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError, NonNullList
from ...core.validators import validate_one_of_args_is_in_mutation
from ...discount.dataloaders import load_discounts
from ...meta.mutations import MetadataInput
from ...order.types import Order
from ...plugins.dataloaders import load_plugin_manager
from ...site.dataloaders import load_site
from ...utils import get_user_or_app_from_context
from ..types import Checkout
from .utils import get_checkout


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
        metadata = NonNullList(
            MetadataInput,
            description=(
                "Fields required to update the checkout metadata." + ADDED_IN_38
            ),
            required=False,
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
        checkout_info: CheckoutInfo,
        lines: Iterable[CheckoutLineInfo],
    ):
        """Validate checkout addresses.

        Mutations for updating addresses have option to turn off a validation. To keep
        consistency, we need to validate it. This will confirm that we have a correct
        address and we can finalize a checkout. In case when address fields
        normalization was turned off, we apply it here.
        Raises ValidationError when any address is not correct.
        """
        shipping_address = checkout_info.shipping_address
        billing_address = checkout_info.billing_address

        if is_shipping_required(lines):
            clean_checkout_shipping(checkout_info, lines, CheckoutErrorCode)
            if shipping_address:
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

    @staticmethod
    def compare_order_data(order_data_1, order_data_2):
        order_total_check = (
            order_data_1["total"].gross.amount == order_data_2["total"].gross.amount
        )
        order_lines_quantity_check = len(order_data_1["lines"]) == len(
            order_data_2["lines"]
        )
        variants_id_1 = [line.variant.id for line in order_data_1["lines"]]
        order_lines_check = all(
            [line.variant.id in variants_id_1 for line in order_data_2["lines"]]
        )
        return order_total_check and order_lines_quantity_check and order_lines_check

    @staticmethod
    def reserve_stocks_without_availability_check(
        checkout_info: CheckoutInfo,
        lines: Iterable[CheckoutLineInfo],
    ):
        """Add additional temporary reservation for stock.

        Due to unlocking rows, for the time of external payment call, it prevents users
        ordering the same product, in the same time, which is out of stock.
        """
        variants = [line.variant for line in lines]
        stocks = Stock.objects.get_variants_stocks_for_country(
            country_code=checkout_info.get_country(),
            channel_slug=checkout_info.channel,
            products_variants=variants,
        )
        variants_stocks_map = {stock.product_variant_id: stock for stock in stocks}

        reservations = []
        for line in lines:
            if line.variant.id in variants_stocks_map:
                reservations.append(
                    Reservation(
                        quantity_reserved=line.line.quantity,
                        reserved_until=timezone.now()
                        + timedelta(seconds=settings.RESERVE_DURATION),
                        stock=variants_stocks_map[line.variant.id],
                        checkout_line=line.line,
                    )
                )
        Reservation.objects.bulk_create(reservations)

    @classmethod
    def prepare_and_validate_checkout_info(
        cls, _root, info, checkout_id=None, token=None, id=None, **data
    ):
        # DEPRECATED
        validate_one_of_args_is_in_mutation(
            CheckoutErrorCode, "checkout_id", checkout_id, "token", token, "id", id
        )

        result = {}
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
                result["checkout_complete"] = CheckoutComplete(
                    order=order, confirmation_needed=False, confirmation_data={}
                )
                return result
            raise e

        metadata = data.get("metadata")
        if metadata is not None:
            cls.check_metadata_permissions(
                info,
                id or checkout_id or graphene.Node.to_global_id("Checkout", token),
            )
            cls.validate_metadata_keys(metadata)

        validate_checkout_email(checkout)

        manager = load_plugin_manager(info.context)

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

        cls.validate_checkout_addresses(checkout_info, lines)

        requestor = get_user_or_app_from_context(info.context)
        if requestor and requestor.has_perm(AccountPermissions.IMPERSONATE_USER):
            # Allow impersonating user and process a checkout by using user details
            # assigned to checkout.
            customer = checkout.user
        else:
            customer = info.context.user

        result["checkout_info"] = checkout_info
        result["lines"] = lines
        result["discounts"] = discounts
        result["customer"] = customer
        result["manager"] = manager
        result["site"] = load_site(info.context)
        result["tracking_code"] = analytics.get_client_id(info.context)

        return result

    @classmethod
    def perform_mutation(
        cls, _root, info, store_source, checkout_id=None, token=None, id=None, **data
    ):
        with transaction_with_commit_on_errors():
            prepayment_info = cls.prepare_and_validate_checkout_info(
                _root, info, checkout_id, token, id, **data
            )

            if prepayment_info.get("checkout_complete"):
                return prepayment_info["checkout_complete"]

            payment, customer_id, order_data = complete_checkout_pre_payment_part(
                manager=prepayment_info["manager"],
                checkout_info=prepayment_info["checkout_info"],
                lines=prepayment_info["lines"],
                discounts=prepayment_info["discounts"],
                user=prepayment_info["customer"],
                site_settings=prepayment_info["site"].settings,
                tracking_code=prepayment_info["tracking_code"],
                redirect_url=data.get("redirect_url"),
            )

            cls.reserve_stocks_without_availability_check(
                prepayment_info["checkout_info"], prepayment_info["lines"]
            )

        # Process payments out of transaction to unlock stock rows for another user,
        # who potentially can order the same product variants.
        txn = None
        if payment:
            txn = process_payment(
                payment=payment,
                customer_id=customer_id,
                store_source=store_source,
                payment_data=data.get("payment_data", {}),
                order_data=order_data,
                manager=prepayment_info["manager"],
                channel_slug=prepayment_info["checkout_info"].channel.slug,
            )

        with transaction_with_commit_on_errors():
            # Run pre-payment checks to make sure, that nothing has changed to the
            # checkout, during processing payment.
            try:
                post_payment_info = cls.prepare_and_validate_checkout_info(
                    _root, info, checkout_id, token, id, **data
                )

                if post_payment_info.get("checkout_complete"):
                    return post_payment_info["checkout_complete"]
            except ValidationError as e:
                release_voucher_usage(
                    order_data.get("voucher"), order_data.get("user_email")
                )
                gateway.payment_refund_or_void(
                    payment,
                    prepayment_info["manager"],
                    channel_slug=prepayment_info["checkout_info"].channel.slug,
                )
                raise e

            post_payment_info["checkout_info"].checkout.voucher_code = None
            _, _, post_payment_order_data = complete_checkout_pre_payment_part(
                manager=post_payment_info["manager"],
                checkout_info=post_payment_info["checkout_info"],
                lines=post_payment_info["lines"],
                discounts=post_payment_info["discounts"],
                user=post_payment_info["customer"],
                site_settings=post_payment_info["site"].settings,
                tracking_code=post_payment_info["tracking_code"],
                redirect_url=data.get("redirect_url"),
            )

            if cls.compare_order_data(order_data, post_payment_order_data):
                (
                    order,
                    action_required,
                    action_data,
                ) = complete_checkout_post_payment_part(
                    manager=post_payment_info["manager"],
                    checkout_info=post_payment_info["checkout_info"],
                    lines=post_payment_info["lines"],
                    payment=payment,
                    txn=txn,
                    order_data=order_data,
                    user=post_payment_info["customer"],
                    app=load_app(info.context),
                    site_settings=post_payment_info["site"].settings,
                    metadata_list=data.get("metadata"),
                )
            else:
                release_voucher_usage(
                    order_data.get("voucher"), order_data.get("user_email")
                )
                gateway.payment_refund_or_void(
                    payment,
                    prepayment_info["manager"],
                    channel_slug=prepayment_info["checkout_info"].channel.slug,
                )
                raise ValidationError("Checkout has changed during payment processing")

        # If gateway returns information that additional steps are required we need
        # to inform the frontend and pass all required data
        return CheckoutComplete(
            order=order,
            confirmation_needed=action_required,
            confirmation_data=action_data,
        )

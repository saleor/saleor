from collections.abc import Iterable

import graphene
from django.core.exceptions import ValidationError

from ....checkout import AddressType
from ....checkout.checkout_cleaner import (
    clean_checkout_shipping,
    validate_checkout_email,
)
from ....checkout.complete_checkout import complete_checkout
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import (
    CheckoutInfo,
    CheckoutLineInfo,
    fetch_checkout_info,
    fetch_checkout_lines,
)
from ....checkout.utils import is_shipping_required
from ....order import models as order_models
from ....permission.enums import AccountPermissions
from ....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ...account.i18n import I18nMixin
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_34, ADDED_IN_38, DEPRECATED_IN_3X_INPUT
from ...core.doc_category import DOC_CATEGORY_CHECKOUT
from ...core.fields import JSONString
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError, NonNullList
from ...core.utils import CHECKOUT_CALCULATE_TAXES_MESSAGE, WebhookEventInfo
from ...core.validators import validate_one_of_args_is_in_mutation
from ...meta.inputs import MetadataInput
from ...order.types import Order
from ...plugins.dataloaders import get_plugin_manager_promise
from ...site.dataloaders import get_site_promise
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
            "Completes the checkout. As a result a new order is created. "
            "The mutation allows to create the unpaid order when setting "
            "`orderSettings.allowUnpaidOrders` for given `Channel` is set to `true`. "
            "When `orderSettings.allowUnpaidOrders` is set to `false`, checkout can "
            "be completed only when attached `Payment`/`TransactionItem`s fully cover "
            "the checkout's total. "
            "When processing the checkout with `Payment`, in case of required "
            "additional confirmation step like 3D secure, the `confirmationNeeded` "
            "flag will be set to True and no order will be created until payment is "
            "confirmed with second call of this mutation."
        )
        doc_category = DOC_CATEGORY_CHECKOUT
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
                description=(
                    "Optionally triggered when cached external shipping methods are "
                    "invalid."
                ),
            ),
            WebhookEventInfo(
                type=WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS,
                description=(
                    "Optionally triggered when cached filtered shipping methods are "
                    "invalid."
                ),
            ),
            WebhookEventInfo(
                type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
                description=CHECKOUT_CALCULATE_TAXES_MESSAGE,
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.ORDER_CREATED,
                description="Triggered when order is created.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.NOTIFY_USER,
                description="A notification for order placement.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.NOTIFY_USER,
                description="A staff notification for order placement.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.ORDER_UPDATED,
                description=(
                    "Triggered when order received the update after placement."
                ),
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.ORDER_PAID,
                description="Triggered when newly created order is paid.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.ORDER_FULLY_PAID,
                description="Triggered when newly created order is fully paid.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.ORDER_CONFIRMED,
                description=(
                    "Optionally triggered when newly created order are automatically "
                    "marked as confirmed."
                ),
            ),
        ]

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
                if not shipping_address.validation_skipped:
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
        if not billing_address.validation_skipped:
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
    def perform_mutation(  # type: ignore[override]
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        checkout_id=None,
        id=None,
        metadata=None,
        payment_data=None,
        redirect_url=None,
        store_source,
        token=None,
    ):
        # DEPRECATED
        validate_one_of_args_is_in_mutation(
            "checkout_id", checkout_id, "token", token, "id", id
        )

        try:
            checkout = get_checkout(
                cls, info, checkout_id=checkout_id, token=token, id=id
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
        if metadata is not None:
            cls.check_metadata_permissions(
                info,
                id or checkout_id or graphene.Node.to_global_id("Checkout", token),
            )
            cls.validate_metadata_keys(metadata)

        validate_checkout_email(checkout)

        manager = get_plugin_manager_promise(info.context).get()
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
        checkout_info = fetch_checkout_info(checkout, lines, manager)

        cls.validate_checkout_addresses(checkout_info, lines)

        requestor = get_user_or_app_from_context(info.context)
        if requestor and requestor.has_perm(AccountPermissions.IMPERSONATE_USER):
            # Allow impersonating user and process a checkout by using user details
            # assigned to checkout.
            customer = checkout.user
        else:
            customer = info.context.user

        site = get_site_promise(info.context).get()

        order, action_required, action_data = complete_checkout(
            checkout_info=checkout_info,
            lines=lines,
            manager=manager,
            payment_data=payment_data or {},
            store_source=store_source,
            user=customer,
            app=get_app_promise(info.context).get(),
            site_settings=site.settings,
            redirect_url=redirect_url,
            metadata_list=metadata,
        )

        # If gateway returns information that additional steps are required we need
        # to inform the frontend and pass all required data
        return CheckoutComplete(
            order=order,
            confirmation_needed=action_required,
            confirmation_data=action_data,
        )

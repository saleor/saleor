import graphene
from django.core.exceptions import ValidationError

from ....checkout.checkout_cleaner import validate_checkout
from ....checkout.complete_checkout import create_order_from_checkout
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....core.exceptions import GiftCardNotApplicable, InsufficientStock
from ....core.taxes import TaxDataError
from ....discount.models import NotApplicable
from ....permission.enums import CheckoutPermissions
from ....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_32, ADDED_IN_38
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.types import Error, NonNullList
from ...core.utils import CHECKOUT_CALCULATE_TAXES_MESSAGE, WebhookEventInfo
from ...meta.inputs import MetadataInput
from ...order.types import Order
from ...plugins.dataloaders import get_plugin_manager_promise
from ..enums import OrderCreateFromCheckoutErrorCode
from ..types import Checkout
from ..utils import prepare_insufficient_stock_checkout_validation_error


class OrderCreateFromCheckoutError(Error):
    code = OrderCreateFromCheckoutErrorCode(
        description="The error code.", required=True
    )
    variants = graphene.List(
        graphene.NonNull(graphene.ID),
        description="List of variant IDs which causes the error.",
        required=False,
    )
    lines = graphene.List(
        graphene.NonNull(graphene.ID),
        description="List of line Ids which cause the error.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderCreateFromCheckout(BaseMutation):
    order = graphene.Field(Order, description="Placed order.")

    class Arguments:
        id = graphene.ID(
            required=True,
            description="ID of a checkout that will be converted to an order.",
        )
        remove_checkout = graphene.Boolean(
            description=(
                "Determines if checkout should be removed after creating an order. "
                "Default true."
            ),
            default_value=True,
        )
        private_metadata = NonNullList(
            MetadataInput,
            description=(
                "Fields required to update the checkout private metadata." + ADDED_IN_38
            ),
            required=False,
        )
        metadata = NonNullList(
            MetadataInput,
            description=(
                "Fields required to update the checkout metadata." + ADDED_IN_38
            ),
            required=False,
        )

    class Meta:
        auto_permission_message = False
        description = (
            "Create new order from existing checkout. Requires the "
            "following permissions: AUTHENTICATED_APP and HANDLE_CHECKOUTS."
            + ADDED_IN_32
        )
        doc_category = DOC_CATEGORY_ORDERS
        object_type = Order
        permissions = (CheckoutPermissions.HANDLE_CHECKOUTS,)
        error_type_class = OrderCreateFromCheckoutError
        support_meta_field = True
        support_private_meta_field = True
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
    def check_permissions(cls, context, permissions=None, **data):
        """Determine whether app has rights to perform this mutation."""
        permissions = permissions or cls._meta.permissions
        app = getattr(context, "app", None)
        if app:
            return app.has_perms(permissions)
        return False

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        id,
        metadata=None,
        private_metadata=None,
        remove_checkout,
    ):
        user = info.context.user
        checkout = cls.get_node_or_error(
            info,
            id,
            field="id",
            only_type=Checkout,
            code=OrderCreateFromCheckoutErrorCode.CHECKOUT_NOT_FOUND.value,
        )

        if cls._meta.support_meta_field and metadata is not None:
            cls.check_metadata_permissions(info, id)
            cls.validate_metadata_keys(metadata)
        if cls._meta.support_private_meta_field and private_metadata is not None:
            cls.check_metadata_permissions(info, id, private=True)
            cls.validate_metadata_keys(private_metadata)

        manager = get_plugin_manager_promise(info.context).get()
        checkout_lines, unavailable_variant_pks = fetch_checkout_lines(checkout)
        checkout_info = fetch_checkout_info(checkout, checkout_lines, manager)

        validate_checkout(
            checkout_info=checkout_info,
            lines=checkout_lines,
            unavailable_variant_pks=unavailable_variant_pks,
            manager=manager,
        )
        app = get_app_promise(info.context).get()
        try:
            order = create_order_from_checkout(
                checkout_info=checkout_info,
                manager=manager,
                user=user,
                app=app,
                delete_checkout=remove_checkout,
                metadata_list=metadata,
                private_metadata_list=private_metadata,
            )
        except NotApplicable:
            code = OrderCreateFromCheckoutErrorCode.VOUCHER_NOT_APPLICABLE.value
            raise ValidationError(
                {
                    "voucher_code": ValidationError(
                        "Voucher not applicable",
                        code=code,
                    )
                }
            )
        except InsufficientStock as e:
            error = prepare_insufficient_stock_checkout_validation_error(e)
            raise error
        except GiftCardNotApplicable as e:
            raise ValidationError({"gift_cards": e})
        except TaxDataError:
            raise ValidationError(
                "Configured Tax App returned invalid response.",
                code=OrderCreateFromCheckoutErrorCode.TAX_ERROR.value,
            )

        return OrderCreateFromCheckout(order=order)

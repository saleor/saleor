from typing import cast

import graphene
from django.core.exceptions import ValidationError

from ....account.models import User
from ....checkout.checkout_cleaner import validate_checkout
from ....checkout.complete_checkout import create_order_from_checkout
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....core import analytics
from ....core.exceptions import GiftCardNotApplicable, InsufficientStock
from ....core.permissions import CheckoutPermissions
from ....discount.models import NotApplicable
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_32, ADDED_IN_38, PREVIEW_FEATURE
from ...core.mutations import BaseMutation
from ...core.types import Error, NonNullList
from ...discount.dataloaders import load_discounts
from ...meta.mutations import MetadataInput
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
            + PREVIEW_FEATURE
        )
        object_type = Order
        permissions = (CheckoutPermissions.HANDLE_CHECKOUTS,)
        error_type_class = OrderCreateFromCheckoutError
        support_meta_field = True
        support_private_meta_field = True

    @classmethod
    def check_permissions(cls, context, permissions=None):
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
        remove_checkout
    ):
        user = info.context.user
        user = cast(User, user)
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

        tracking_code = analytics.get_client_id(info.context)

        manager = get_plugin_manager_promise(info.context).get()
        discounts = load_discounts(info.context)
        checkout_lines, unavailable_variant_pks = fetch_checkout_lines(checkout)
        checkout_info = fetch_checkout_info(
            checkout, checkout_lines, discounts, manager
        )

        validate_checkout(
            checkout_info=checkout_info,
            lines=checkout_lines,
            unavailable_variant_pks=unavailable_variant_pks,
            discounts=discounts,
            manager=manager,
        )
        app = get_app_promise(info.context).get()
        try:
            order = create_order_from_checkout(
                checkout_info=checkout_info,
                checkout_lines=checkout_lines,
                discounts=discounts,
                manager=manager,
                user=user,
                app=app,
                tracking_code=str(tracking_code),
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

        return OrderCreateFromCheckout(order=order)

from django.conf import settings

from ..core import ResolveInfo
from ..core.context import get_database_connection_name
from ..core.descriptions import ADDED_IN_36
from ..core.doc_category import DOC_CATEGORY_CHECKOUT
from ..core.types import NonNullList, SubscriptionObjectType
from ..plugins.dataloaders import plugin_manager_promise_callback
from ..shipping.types import ShippingMethod
from ..webhook.subscription_types import (
    CheckoutBase,
    Event,
)


def resolve_shipping_methods_for_checkout(
    info: ResolveInfo,
    checkout,
    manager,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    from ...checkout.fetch import (
        fetch_checkout_info,
        fetch_checkout_lines,
        get_all_shipping_methods_list,
    )

    lines, _ = fetch_checkout_lines(checkout)
    shipping_channel_listings = checkout.channel.shipping_method_listings.all()
    checkout_info = fetch_checkout_info(
        checkout,
        lines,
        manager,
        shipping_channel_listings,
        database_connection_name=database_connection_name,
    )
    all_shipping_methods = get_all_shipping_methods_list(
        checkout_info,
        checkout.shipping_address,
        lines,
        shipping_channel_listings,
        manager,
        database_connection_name=database_connection_name,
    )
    return all_shipping_methods


class ShippingListMethodsForCheckout(SubscriptionObjectType, CheckoutBase):
    shipping_methods = NonNullList(
        ShippingMethod,
        description="Shipping methods that can be used with this checkout."
        + ADDED_IN_36,
    )

    @staticmethod
    @plugin_manager_promise_callback
    def resolve_shipping_methods(root, info: ResolveInfo, manager):
        _, checkout = root
        database_connection_name = get_database_connection_name(info.context)
        return resolve_shipping_methods_for_checkout(
            info, checkout, manager, database_connection_name
        )

    class Meta:
        root_type = None
        enable_dry_run = False
        interfaces = (Event,)
        description = "List shipping methods for checkout." + ADDED_IN_36
        doc_category = DOC_CATEGORY_CHECKOUT

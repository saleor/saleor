from promise import Promise

from ...checkout import models
from ...checkout.utils import get_valid_shipping_methods_for_checkout
from ...core.permissions import AccountPermissions, CheckoutPermissions
from ...core.tracing import traced_resolver
from ..account.dataloaders import AddressByIdLoader
from ..channel.dataloaders import ChannelByIdLoader
from ..discount.dataloaders import DiscountsByDateTimeLoader
from ..shipping.dataloaders import (
    ShippingMethodByIdLoader,
    ShippingMethodChannelListingByShippingMethodIdAndChannelSlugLoader,
)
from ..shipping.utils import (
    annotate_active_shipping_methods,
    annotate_shipping_methods_with_price,
    convert_shipping_method_model_to_dataclass,
    wrap_with_channel_context,
)
from ..utils import get_user_or_app_from_context
from .dataloaders import (
    CheckoutInfoByCheckoutTokenLoader,
    CheckoutLinesInfoByCheckoutTokenLoader,
)


def resolve_checkout_lines():
    queryset = models.CheckoutLine.objects.all()
    return queryset


def resolve_checkouts(channel_slug):
    queryset = models.Checkout.objects.all()
    if channel_slug:
        queryset = queryset.filter(channel__slug=channel_slug)
    return queryset


@traced_resolver
def resolve_checkout(info, token):
    checkout = models.Checkout.objects.filter(token=token).first()

    if checkout is None:
        return None

    # resolve checkout in active channel
    if checkout.channel.is_active:
        # resolve checkout for anonymous customer
        if not checkout.user:
            return checkout

        # resolve checkout for logged-in customer
        if checkout.user == info.context.user:
            return checkout

    # resolve checkout for staff user
    requester = get_user_or_app_from_context(info.context)

    has_manage_checkout = requester.has_perm(CheckoutPermissions.MANAGE_CHECKOUTS)
    has_impersonate_user = requester.has_perm(AccountPermissions.IMPERSONATE_USER)
    if has_manage_checkout or has_impersonate_user:
        return checkout

    return None


def _resolve_checkout_excluded_shipping_methods(
    root,
    channel_listings,
    shipping_methods,
    address,
    channel_slug,
    manager,
    info,
):
    cache_key = "__fetched_shipping_methods"
    if hasattr(root, cache_key):
        return getattr(root, cache_key)

    annotate_shipping_methods_with_price(
        shipping_methods,
        channel_listings,
        address,
        channel_slug,
        manager,
    )
    shipping_method_dataclasses = [
        convert_shipping_method_model_to_dataclass(shipping)
        for shipping in shipping_methods
    ]
    excluded_shipping_methods = manager.excluded_shipping_methods_for_checkout(
        root, shipping_method_dataclasses
    )
    annotate_active_shipping_methods(
        shipping_methods,
        excluded_shipping_methods,
    )
    available_with_channel_context = wrap_with_channel_context(
        shipping_methods,
        channel_slug,
    )

    setattr(root, cache_key, available_with_channel_context)
    return getattr(root, cache_key)


def resolve_checkout_shipping_methods(
    root: models.Checkout, info, include_active_only=False
):
    def calculate_shipping_methods(data):
        address, lines, checkout_info, discounts, channel = data
        if not address:
            return []
        channel_slug = channel.slug
        manager = info.context.plugins
        subtotal = manager.calculate_checkout_subtotal(
            checkout_info, lines, address, discounts
        )
        subtotal -= checkout_info.checkout.discount
        available = get_valid_shipping_methods_for_checkout(
            checkout_info,
            lines,
            subtotal=subtotal,
            country_code=address.country.code,
        )
        if available is None:
            return []
        available_ids = available.values_list("id", flat=True)

        def map_shipping_method_with_channel(shippings):
            def apply_price_to_shipping_method(channel_listings):
                available_with_channel_context = (
                    _resolve_checkout_excluded_shipping_methods(
                        root,
                        channel_listings,
                        shippings,
                        address,
                        channel_slug,
                        manager,
                        info,
                    )
                )
                if include_active_only:
                    available_with_channel_context = [
                        shipping
                        for shipping in available_with_channel_context
                        if shipping.node.active
                    ]
                return available_with_channel_context

            map_shipping_method_and_channel = (
                (shipping_method_id, channel_slug)
                for shipping_method_id in available_ids
            )
            return (
                ShippingMethodChannelListingByShippingMethodIdAndChannelSlugLoader(
                    info.context
                )
                .load_many(map_shipping_method_and_channel)
                .then(apply_price_to_shipping_method)
            )

        return (
            ShippingMethodByIdLoader(info.context)
            .load_many(available_ids)
            .then(map_shipping_method_with_channel)
        )

    channel = ChannelByIdLoader(info.context).load(root.channel_id)
    address = (
        AddressByIdLoader(info.context).load(root.shipping_address_id)
        if root.shipping_address_id
        else None
    )
    lines = CheckoutLinesInfoByCheckoutTokenLoader(info.context).load(root.token)
    checkout_info = CheckoutInfoByCheckoutTokenLoader(info.context).load(root.token)
    discounts = DiscountsByDateTimeLoader(info.context).load(info.context.request_time)

    return Promise.all([address, lines, checkout_info, discounts, channel]).then(
        calculate_shipping_methods
    )

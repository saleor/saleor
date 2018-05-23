"""Checkout session state management."""
from datetime import date
from functools import wraps

from django.db import transaction
from django.utils.encoding import smart_text
from django.utils.translation import get_language

from ...account.utils import store_user_address
from ...core import analytics
from ...core.utils.taxes import get_taxes_for_country
from ...discount.models import Voucher
from ...discount.utils import increase_voucher_usage
from ...order.models import Order
from ...order.utils import add_variant_to_order
from ..models import Cart
from ..utils import get_or_empty_db_cart
from .utils import get_voucher_for_cart

STORAGE_SESSION_KEY = 'checkout_storage'


class Checkout:
    """Represents a checkout session.

    This object acts a temporary storage for the entire checkout session. An
    order instance is only created when the user confirms their order and is
    ready to pay.

    `VERSION` is used to prevent code trying to work with incompatible
    checkout structures.

    The `modified` attribute keeps track of when checkout state changes and
    needs to be saved.
    """

    VERSION = '1.0.0'

    def __init__(self, cart, user, discounts, taxes, tracking_code):
        self.modified = False
        self.cart = cart
        self.user = user
        self.discounts = discounts
        self.taxes = taxes
        self.tracking_code = tracking_code
        self.storage = {'version': self.VERSION}

    @classmethod
    def from_storage(
            cls, storage_data, cart, user, discounts, taxes, tracking_code):
        """Restore a previously serialized checkout session.

        `storage_data` is the value previously returned by
        `Checkout.for_storage()`.
        """
        checkout = cls(cart, user, discounts, taxes, tracking_code)
        checkout.storage = storage_data
        try:
            version = checkout.storage['version']
        except (TypeError, KeyError):
            version = None
        if version != cls.VERSION:
            checkout.storage = {'version': cls.VERSION}
        return checkout

    def for_storage(self):
        """Serialize a checkout session to allow persistence.

        The session can later be restored using `Checkout.from_storage()`.
        """
        return self.storage

    def clear_storage(self):
        """Discard the entire state."""
        self.storage = None
        self.modified = True

    @transaction.atomic
    def create_order(self):
        """Create an order from the checkout session.

        Each order will get a private copy of both the billing and the shipping
        address (if shipping ).

        If any of the addresses is new and the user is logged in the address
        will also get saved to that user's address book.

        Current user's language is saved in the order so we can later determine
        which language to use when sending email.
        """
        # FIXME: save locale along with the language
        voucher = get_voucher_for_cart(
            self.cart,
            vouchers=Voucher.objects.active(
                date=date.today()).select_for_update())

        if self.cart.voucher_code is not None and voucher is None:
            # Voucher expired in meantime, abort order placement
            return None

        billing_address = self.cart.billing_address

        if self.cart.is_shipping_required():
            shipping_address = self.cart.shipping_address
            shipping_method = self.cart.shipping_method
            shipping_method_name = smart_text(shipping_method)
        else:
            shipping_address = None
            shipping_method = None
            shipping_method_name = None

        if self.cart.user:
            if (
                shipping_address and
                shipping_address not in self.cart.user.addresses.all()
            ):
                store_user_address(
                    self.user, shipping_address, shipping=True)
            if billing_address not in self.cart.user.addresses.all():
                store_user_address(
                    self.user, billing_address, billing=True)
            if shipping_address:
                shipping_address = shipping_address.get_copy()
            billing_address = billing_address.get_copy()

        taxes = self.get_taxes()

        order_data = {
            'language_code': get_language(),
            'billing_address': billing_address,
            'shipping_address': shipping_address,
            'tracking_client_id': self.tracking_code,
            'shipping_method': shipping_method,
            'shipping_method_name': shipping_method_name,
            'shipping_price': self.cart.get_shipping_price(taxes),
            'total': self.get_total()}

        if self.user.is_authenticated:
            order_data['user'] = self.user
            order_data['user_email'] = self.user.email
        else:
            order_data['user_email'] = self.cart.user_email

        if voucher is not None:
            order_data['voucher'] = voucher
            order_data['discount_amount'] = self.cart.discount_amount
            order_data['discount_name'] = self.cart.discount_name

        order = Order.objects.create(**order_data)

        for line in self.cart.lines.all():
            add_variant_to_order(
                order, line.variant, line.quantity, self.discounts, taxes,
                add_to_existing=False)

        if voucher is not None:
            increase_voucher_usage(voucher)

        if self.cart.note:
            order.notes.create(user=order.user, content=self.cart.note)

        return order

    def get_subtotal(self):
        """Calculate order total without shipping and discount."""
        return self.cart.get_total(self.discounts, self.get_taxes())

    def get_total(self):
        """Calculate order total with shipping and discount amount."""
        total = self.get_subtotal()
        total += self.cart.get_shipping_price(self.get_taxes())
        total -= self.cart.discount_amount
        return total

    def get_taxes(self):
        """Return taxes based on shipping address (if set) or IP country."""
        if self.cart.shipping_address:
            return get_taxes_for_country(self.cart.shipping_address.country)

        return self.taxes


def load_checkout(view):
    """Decorate view with checkout session and cart for each request.

    Any views decorated by this will change their signature from
    `func(request)` to `func(request, cart, checkout)`.
    """
    # FIXME: behave like middleware and assign checkout and cart to request
    # instead of changing the view signature
    @wraps(view)
    @get_or_empty_db_cart(Cart.objects.for_display())
    def func(request, cart):
        try:
            session_data = request.session[STORAGE_SESSION_KEY]
        except KeyError:
            session_data = ''
        tracking_code = analytics.get_client_id(request)
        checkout = Checkout.from_storage(
            session_data, cart, request.user, request.discounts, request.taxes,
            tracking_code)
        response = view(request, cart, checkout)
        if checkout.modified:
            request.session[STORAGE_SESSION_KEY] = checkout.for_storage()
        return response

    return func

"""Checkout session state management."""
from datetime import date
from functools import wraps

from django.conf import settings
from django.db import transaction
from django.forms.models import model_to_dict
from django.utils.encoding import smart_text
from django.utils.translation import get_language
from prices import Money, TaxedMoney

from ..account.models import Address
from ..account.utils import store_user_address
from ..cart.models import Cart
from ..cart.utils import get_or_empty_db_cart
from ..core import analytics
from ..discount.models import NotApplicable, Voucher
from ..discount.utils import increase_voucher_usage
from ..order.models import Order
from ..order.utils import add_variant_to_order
from ..shipping.models import ANY_COUNTRY, ShippingMethodCountry
from .utils import get_voucher_discount_for_checkout

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

    def __init__(self, cart, user, tracking_code):
        self.modified = False
        self.cart = cart
        self.storage = {'version': self.VERSION}
        self.tracking_code = tracking_code
        self.user = user
        self.discounts = cart.discounts
        self._shipping_method = None
        self._shipping_address = None

    @classmethod
    def from_storage(cls, storage_data, cart, user, tracking_code):
        """Restore a previously serialized checkout session.

        `storage_data` is the value previously returned by
        `Checkout.for_storage()`.
        """
        checkout = cls(cart, user, tracking_code)
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

    def _get_address_from_storage(self, key):
        address_data = self.storage.get(key)
        if address_data is not None and address_data.get('id'):
            try:
                return Address.objects.get(id=address_data['id'])
            except Address.DoesNotExist:
                return None
        elif address_data:
            return Address(**address_data)
        return None

    @property
    def is_shipping_required(self):
        """Return `True` if this checkout session needs shipping."""
        return self.cart.is_shipping_required()

    @property
    def shipping_address(self):
        """Return a shipping address if any."""
        if self._shipping_address is None:
            address = self._get_address_from_storage('shipping_address')
            if address is None and self.user.is_authenticated:
                address = self.user.default_shipping_address
            self._shipping_address = address
        return self._shipping_address

    @shipping_address.setter
    def shipping_address(self, address):
        address_data = model_to_dict(address)
        phone_number = address_data.get('phone')
        if phone_number:
            address_data['phone'] = str(address_data['phone'])
        address_data['country'] = smart_text(address_data['country'])
        self.storage['shipping_address'] = address_data
        self.modified = True
        self._shipping_address = address

    @property
    def shipping_method(self):
        """Return a shipping method if any."""
        if self._shipping_method is None:
            shipping_address = self.shipping_address
            if shipping_address is None:
                return None
            shipping_method_country_id = self.storage.get(
                'shipping_method_country_id')
            if shipping_method_country_id is None:
                return None
            try:
                shipping_method_country = ShippingMethodCountry.objects.get(
                    id=shipping_method_country_id)
            except ShippingMethodCountry.DoesNotExist:
                return None
            shipping_country_code = shipping_address.country.code
            allowed_codes = [ANY_COUNTRY, shipping_country_code]
            if shipping_method_country.country_code not in allowed_codes:
                return None
            self._shipping_method = shipping_method_country
        return self._shipping_method

    @shipping_method.setter
    def shipping_method(self, shipping_method_country):
        self.storage['shipping_method_country_id'] = shipping_method_country.id
        self.modified = True
        self._shipping_method = shipping_method_country

    @property
    def email(self):
        """Return the customer email if any."""
        return self.storage.get('email')

    @email.setter
    def email(self, email):
        self.storage['email'] = email
        self.modified = True

    @property
    def note(self):
        return self.storage.get('note')

    @note.setter
    def note(self, note):
        self.storage['note'] = note
        self.modified = True

    @property
    def billing_address(self):
        """Return the billing addres if any."""
        address = self._get_address_from_storage('billing_address')
        if address is not None:
            return address
        elif (self.user.is_authenticated and
              self.user.default_billing_address):
            return self.user.default_billing_address
        elif self.shipping_address:
            return self.shipping_address
        return None

    @billing_address.setter
    def billing_address(self, address):
        address_data = model_to_dict(address)
        address_data['country'] = smart_text(address_data['country'])
        self.storage['billing_address'] = address_data
        self.modified = True

    @property
    def discount(self):
        """Return a discount if any."""
        value = self.storage.get('discount_value')
        currency = self.storage.get('discount_currency')
        if value is not None and currency is not None:
            return Money(value, currency)
        return None

    @discount.setter
    def discount(self, discount):
        self.storage['discount_value'] = smart_text(discount.amount)
        self.storage['discount_currency'] = discount.currency
        self.modified = True

    @discount.deleter
    def discount(self):
        if 'discount_value' in self.storage:
            del self.storage['discount_value']
            self.modified = True
        if 'discount_currency' in self.storage:
            del self.storage['discount_currency']
            self.modified = True

    @property
    def discount_name(self):
        """Return a discount name if any."""
        return self.storage.get('discount_name')

    @discount_name.setter
    def discount_name(self, discount_name):
        self.storage['discount_name'] = discount_name
        self.modified = True

    @discount_name.deleter
    def discount_name(self):
        if 'discount_name' in self.storage:
            del self.storage['discount_name']
            self.modified = True

    @property
    def voucher_code(self):
        """Return a discount voucher code if any."""
        return self.storage.get('voucher_code')

    @voucher_code.setter
    def voucher_code(self, voucher_code):
        self.storage['voucher_code'] = voucher_code
        self.modified = True

    @voucher_code.deleter
    def voucher_code(self):
        if 'voucher_code' in self.storage:
            del self.storage['voucher_code']
            self.modified = True

    @property
    def is_shipping_same_as_billing(self):
        """Return `True` if shipping and billing addresses are identical."""
        return self.shipping_address == self.billing_address

    def _add_to_user_address_book(self, address, is_billing=False,
                                  is_shipping=False):
        if self.user.is_authenticated:
            store_user_address(
                self.user, address, shipping=is_shipping,
                billing=is_billing)

    def _save_order_billing_address(self):
        return self.billing_address.get_copy()

    def _save_order_shipping_address(self):
        return self.shipping_address.get_copy()

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
        voucher = self._get_voucher(
            vouchers=Voucher.objects.active(date=date.today())
            .select_for_update())
        if self.voucher_code is not None and voucher is None:
            # Voucher expired in meantime, abort order placement
            return None

        if self.is_shipping_required:
            shipping_address = self._save_order_shipping_address()
            self._add_to_user_address_book(
                self.shipping_address, is_shipping=True)
        else:
            shipping_address = None
        billing_address = self._save_order_billing_address()
        self._add_to_user_address_book(
            self.billing_address, is_billing=True)

        if self.shipping_method:
            shipping_price = self.shipping_method.get_total_price()
        else:
            shipping_price = TaxedMoney(
                net=Money(0, settings.DEFAULT_CURRENCY),
                gross=Money(0, settings.DEFAULT_CURRENCY))

        shipping_method_name = (
            smart_text(self.shipping_method) if self.is_shipping_required
            else None)
        order_data = {
            'language_code': get_language(),
            'billing_address': billing_address,
            'shipping_address': shipping_address,
            'tracking_client_id': self.tracking_code,
            'shipping_price': shipping_price,
            'shipping_method_name': shipping_method_name,
            'total': self.get_total()}

        if self.user.is_authenticated:
            order_data['user'] = self.user
            order_data['user_email'] = self.user.email
        else:
            order_data['user_email'] = self.email

        if voucher is not None:
            order_data['voucher'] = voucher
            order_data['discount_amount'] = self.discount
            order_data['discount_name'] = self.discount_name

        order = Order.objects.create(**order_data)

        for line in self.cart.lines.all():
            add_variant_to_order(
                order, line.variant, line.quantity, self.cart.discounts,
                add_to_existing=False)

        if voucher is not None:
            increase_voucher_usage(voucher)

        if self.note is not None and self.note:
            order.notes.create(user=order.user, content=self.note)

        return order

    def _get_voucher(self, vouchers=None):
        voucher_code = self.voucher_code
        if voucher_code is not None:
            if vouchers is None:
                vouchers = Voucher.objects.active(date=date.today())
            try:
                return vouchers.get(code=self.voucher_code)
            except Voucher.DoesNotExist:
                return None
        return None

    def recalculate_discount(self):
        """Recalculate `self.discount` based on the voucher.

        Will clear both voucher and discount if the discount is no longer
        applicable.
        """
        voucher = self._get_voucher()
        if voucher is not None:
            try:
                self.discount = get_voucher_discount_for_checkout(
                    voucher, self)
                self.discount_name = voucher.name
            except NotApplicable:
                del self.discount
                del self.discount_name
                del self.voucher_code
        else:
            del self.discount
            del self.discount_name
            del self.voucher_code

    def get_subtotal(self):
        """Calculate order total without shipping and discount."""
        return self.cart.get_total()

    def get_total(self):
        """Calculate order total with shipping and discount amount."""
        total = self.cart.get_total()
        if self.shipping_method and self.is_shipping_required:
            total += self.shipping_method.get_total_price()
        if self.discount:
            total -= self.discount
        return total


def load_checkout(view):
    """Decorate view with checkout session and cart for each request.

    Any views decorated by this will change their signature from
    `func(request)` to `func(request, checkout, cart)`.
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
            session_data, cart, request.user, tracking_code)
        response = view(request, checkout, cart)
        if checkout.modified:
            request.session[STORAGE_SESSION_KEY] = checkout.for_storage()
        return response

    return func

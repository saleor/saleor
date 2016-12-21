from __future__ import unicode_literals
from functools import wraps

from django.conf import settings
from django.db import transaction
from django.forms.models import model_to_dict
from django.utils.encoding import smart_text
from prices import Price, FixedDiscount

from ..cart.utils import get_or_empty_db_cart
from ..core import analytics
from ..discount.models import Voucher, NotApplicable
from ..order.models import Order
from ..shipping.models import ShippingMethodCountry, ANY_COUNTRY
from ..userprofile.models import Address, User

STORAGE_SESSION_KEY = 'checkout_storage'


class Checkout(object):

    VERSION = '1.0.0'
    modified = False

    def __init__(self, cart, user, tracking_code):
        self.cart = cart
        self.storage = {'version': self.VERSION}
        self.tracking_code = tracking_code
        self.user = user
        self.discounts = cart.discounts

    @classmethod
    def from_storage(cls, storage_data, cart, user, tracking_code):
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
        return self.storage

    def clear_storage(self):
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
        return self.cart.is_shipping_required()

    @property
    def deliveries(self):
        for partition in self.cart.partition():
            if self.shipping_method and partition.is_shipping_required():
                shipping_cost = self.shipping_method.get_total()
            else:
                shipping_cost = Price(0, currency=settings.DEFAULT_CURRENCY)
            total_with_shipping = partition.get_total(
                discounts=self.cart.discounts) + shipping_cost

            partition = [
                (item,
                 item.get_price_per_item(discounts=self.cart.discounts),
                 item.get_total(discounts=self.cart.discounts))
                for item in partition]

            yield partition, shipping_cost, total_with_shipping

    @property
    def shipping_address(self):
        address = self._get_address_from_storage('shipping_address')
        if address is None and self.user.is_authenticated():
            return self.user.default_shipping_address
        return address

    @shipping_address.setter
    def shipping_address(self, address):
        address_data = model_to_dict(address)
        address_data['country'] = smart_text(address_data['country'])
        self.storage['shipping_address'] = address_data
        self.modified = True

    @property
    def shipping_method(self):
        shipping_address = self.shipping_address
        if shipping_address is not None:
            shipping_method_country_id = self.storage.get(
                'shipping_method_country_id')
            if shipping_method_country_id is not None:
                try:
                    shipping_method_country = ShippingMethodCountry.objects.get(
                        id=shipping_method_country_id)
                except ShippingMethodCountry.DoesNotExist:
                    return None
                shipping_country_code = shipping_address.country.code
                if (shipping_method_country.country_code == ANY_COUNTRY or
                        shipping_method_country.country_code == shipping_country_code):
                    return shipping_method_country

    @shipping_method.setter
    def shipping_method(self, shipping_method_country):
        self.storage['shipping_method_country_id'] = shipping_method_country.id
        self.modified = True

    @property
    def email(self):
        return self.storage.get('email')

    @email.setter
    def email(self, email):
        self.storage['email'] = email
        self.modified = True

    @property
    def billing_address(self):
        address = self._get_address_from_storage('billing_address')
        if address is not None:
            return address
        elif self.user.is_authenticated() and self.user.default_billing_address:
            return self.user.default_billing_address
        elif self.shipping_address:
            return self.shipping_address

    @billing_address.setter
    def billing_address(self, address):
        address_data = model_to_dict(address)
        address_data['country'] = smart_text(address_data['country'])
        self.storage['billing_address'] = address_data
        self.modified = True

    @property
    def discount(self):
        value = self.storage.get('discount_value')
        currency = self.storage.get('discount_currency')
        name = self.storage.get('discount_name')
        if value is not None and name is not None and currency is not None:
            amount = Price(value, currency=currency)
            return FixedDiscount(amount, name)

    @discount.setter
    def discount(self, discount):
        amount = discount.amount
        self.storage['discount_value'] = smart_text(amount.net)
        self.storage['discount_currency'] = amount.currency
        self.storage['discount_name'] = discount.name
        self.modified = True

    @discount.deleter
    def discount(self):
        if 'discount_value' in self.storage:
            del self.storage['discount_value']
            self.modified = True
        if 'discount_currency' in self.storage:
            del self.storage['discount_currency']
            self.modified = True
        if 'discount_name' in self.storage:
            del self.storage['discount_name']
            self.modified = True

    @property
    def voucher_code(self):
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
        return Address.objects.are_identical(
            self.shipping_address, self.billing_address)

    def _add_to_user_address_book(self, address, is_billing=False,
                                  is_shipping=False):
        if self.user.is_authenticated():
            User.objects.store_address(
                self.user, address, shipping=is_shipping,
                billing=is_billing)

    def _get_address_copy(self, address):
        address.user = None
        address.pk = None
        address.save()
        return address

    def _save_order_billing_address(self):
        return self._get_address_copy(self.billing_address)

    def _save_order_shipping_address(self):
        return self._get_address_copy(self.shipping_address)

    @transaction.atomic
    def create_order(self):
        voucher = self._get_voucher(
            vouchers=Voucher.objects.active().select_for_update())
        if self.voucher_code is not None and voucher is None:
            # Voucher expired in meantime, abort order placement
            return

        if self.is_shipping_required:
            shipping_address = self._save_order_shipping_address()
            self._add_to_user_address_book(
                self.shipping_address, is_shipping=True)
        else:
            shipping_address = None
        billing_address = self._save_order_billing_address()
        self._add_to_user_address_book(
            self.shipping_address, is_billing=True)

        order_data = {
            'billing_address': billing_address,
            'shipping_address': shipping_address,
            'tracking_client_id': self.tracking_code,
            'total': self.get_total()}

        if self.user.is_authenticated():
            order_data['user'] = self.user
            order_data['user_email'] = self.user.email

        else:
            order_data['user_email'] = self.email

        if voucher is not None:
            discount = self.discount
            order_data['voucher'] = voucher
            order_data['discount_amount'] = discount.amount
            order_data['discount_name'] = discount.name

        order = Order.objects.create(**order_data)

        for partition in self.cart.partition():
            shipping_required = partition.is_shipping_required()
            if shipping_required:
                shipping_price = self.shipping_method.get_total()
                shipping_method_name = smart_text(self.shipping_method)
            else:
                shipping_price = 0
                shipping_method_name = None
            group = order.groups.create(
                shipping_price=shipping_price,
                shipping_method_name=shipping_method_name)
            group.add_items_from_partition(
                partition, discounts=self.cart.discounts)

        if voucher is not None:
            Voucher.objects.increase_usage(voucher)

        return order

    def _get_voucher(self, vouchers=None):
        voucher_code = self.voucher_code
        if voucher_code is not None:
            if vouchers is None:
                vouchers = Voucher.objects.active()
            try:
                return vouchers.get(code=self.voucher_code)
            except Voucher.DoesNotExist:
                return None

    def recalculate_discount(self):
        voucher = self._get_voucher()
        if voucher is not None:
            try:
                self.discount = voucher.get_discount_for_checkout(self)
            except NotApplicable:
                del self.discount
                del self.voucher_code
        else:
            del self.discount
            del self.voucher_code

    def get_subtotal(self):
        zero = Price(0, currency=settings.DEFAULT_CURRENCY)
        cost_iterator = (
            total - shipping_cost
            for shipment, shipping_cost, total in self.deliveries)
        total = sum(cost_iterator, zero)
        return total

    def get_total(self):
        zero = Price(0, currency=settings.DEFAULT_CURRENCY)
        cost_iterator = (
            total
            for shipment, shipping_cost, total in self.deliveries)
        total = sum(cost_iterator, zero)
        return total if self.discount is None else self.discount.apply(total)

    def get_total_shipping(self):
        zero = Price(0, currency=settings.DEFAULT_CURRENCY)
        cost_iterator = (
            shipping_cost
            for shipment, shipping_cost, total in self.deliveries)
        total = sum(cost_iterator, zero)
        return total


def load_checkout(view):
    @wraps(view)
    @get_or_empty_db_cart()
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

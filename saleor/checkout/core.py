from __future__ import unicode_literals
from functools import wraps

from django.conf import settings
from django.db import transaction
from django.forms.models import model_to_dict
from prices import Price

from ..cart import Cart
from ..core import analytics
from ..order.models import Order
from ..shipping.models import ShippingMethodCountry
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
            total_with_shipping = partition.get_total() + shipping_cost
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
        address_data['country'] = str(address_data['country'])
        self.storage['shipping_address'] = address_data
        self.modified = True

    @property
    def shipping_method(self):
        shipping_method_country_id = self.storage.get('shipping_method_country_id')
        if shipping_method_country_id is not None:
            try:
                shipping_method_country = ShippingMethodCountry.objects.get(
                    id=shipping_method_country_id)
            except ShippingMethodCountry.DoesNotExist:
                return None
            shipping_country_code = self.shipping_address.country.code
            any_country = ShippingMethodCountry.ANY_COUNTRY
            if (shipping_method_country.country_code == any_country
                or shipping_method_country.country_code == shipping_country_code):
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
        if address is None and self.user.is_authenticated():
            return self.user.default_billing_address
        return address

    @billing_address.setter
    def billing_address(self, address):
        address_data = model_to_dict(address)
        address_data['country'] = str(address_data['country'])
        self.storage['billing_address'] = address_data
        self.modified = True

    @property
    def is_shipping_same_as_billing(self):
        return Address.objects.are_identical(self.shipping_address, self.billing_address)

    def _save_address(self, address, is_billing=False, is_shipping=False):
        if self.user.is_authenticated() and address.id is None:
            address = User.objects.store_address(
                self.user, address, shipping=is_shipping, billing=is_billing)
        elif address.id is None:
            address.save()
        return address

    @transaction.atomic
    def create_order(self):
        if self.is_shipping_required:
            shipping_address = self._save_address(
                self.shipping_address, is_shipping=True)
        else:
            shipping_address = None
        billing_address = self._save_address(self.billing_address, is_billing=True)
        if self.user.is_authenticated():
            order = Order.objects.create(
                billing_address=billing_address, shipping_address=shipping_address,
                user=self.user, total=self.get_total(),
                tracking_client_id=self.tracking_code)
        else:
            order = Order.objects.create(
                billing_address=billing_address, shipping_address=shipping_address,
                anonymous_user_email=self.email, total=self.get_total(),
                tracking_client_id=self.tracking_code)

        for partition in self.cart.partition():
            shipping_required = partition.is_shipping_required()
            if shipping_required:
                shipping_price = self.shipping_method.get_total()
                shipping_method_name = str(self.shipping_method)
            else:
                shipping_price = 0
                shipping_method_name = None
            group = order.groups.create(
                shipping_required=shipping_required,
                shipping_price=shipping_price,
                shipping_method_name=shipping_method_name)
            group.add_items_from_partition(partition)

        return order

    def get_total(self):
        zero = Price(0, currency=settings.DEFAULT_CURRENCY)
        cost_iterator = (
            total_with_shipping for shipping, shipping_cost, total_with_shipping
            in self.deliveries)
        total = sum(cost_iterator, zero)
        return total


def load_checkout(view):
    @wraps(view)
    def func(request):
        try:
            session_data = request.session[STORAGE_SESSION_KEY]
        except KeyError:
            session_data = ''
        tracking_code = analytics.get_client_id(request)
        cart = Cart.for_session_cart(
            request.cart, discounts=request.discounts)
        checkout = Checkout.from_storage(
            session_data, cart, request.user, tracking_code)
        response = view(request, checkout)
        if checkout.modified:
            request.session[STORAGE_SESSION_KEY] = checkout.for_storage()
        return response

    return func

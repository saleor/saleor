from django.contrib.auth.models import AnonymousUser
from mock import MagicMock
import pytest

from .core import STORAGE_SESSION_KEY
from ..userprofile.models import Address, User
from .steps import ShippingAddressStep, ShippingMethodStep, SummaryStep


NEW_ADDRESS = {
    'first_name': 'Test',
    'last_name': 'Test',
    'street_address_1': 'Test',
    'street_address_2': 'Test',
    'city': 'Test',
    'phone': '12345678',
    'postal_code': '987654',
    'country': 'PL',
    'country_area': '',
    'company_name': 'Test'}

SHIPPING_PREFIX = 'shipping-address'
SUMMARY_PREFIX = 'summary'
USER_EMAIL = 'user@example.com'


class TestUser(User):

    class QuerysetMock(list):
        model = MagicMock()

        def get(self, id):
            pytest.set_trace()
            print "get ********()", id
            print "get ********()", id
            print "get ********()", id
            for address in self._addresses:
                if address.id == id:
                    print "tutaj"
                    return address

    _addresses = QuerysetMock()

    @property
    def addresses(self):
        addresses_mock = MagicMock()
        addresses_mock.all = MagicMock()
        addresses_mock.all.return_value = self._addresses
        return addresses_mock

    @addresses.setter
    def addresses(self, addresses_list):
        for address in addresses_list:
            self._addresses.append(address)


def get_address(address, prefix=''):
    if prefix:
        prefix = '%s-' % (prefix,)

    return {prefix + k: v for k, v in address.items()}


def test_shipping_step_save_address_anonymous_user(rf):
    address = get_address(NEW_ADDRESS, SHIPPING_PREFIX)
    data = dict(address, email=USER_EMAIL)
    request = rf.post('/checkout/', data)
    request.user = AnonymousUser()
    request.session = {STORAGE_SESSION_KEY: {}}
    storage = {}
    step = ShippingAddressStep(request, storage, checkout=MagicMock())
    assert step.forms_are_valid()
    step.save()
    assert isinstance(storage['address'], dict)
    assert storage['email'] == USER_EMAIL


def test_shipping_step_save_address_authenticated_user(rf):
    address = get_address(NEW_ADDRESS, SHIPPING_PREFIX)
    user = TestUser()
    user.addresses = []
    request = rf.post('/checkout/', address)
    request.user = user
    request.session = {STORAGE_SESSION_KEY: {}}
    storage = {}
    step = ShippingAddressStep(request, storage, checkout=MagicMock())
    assert step.forms_are_valid()
    step.save()
    assert isinstance(storage['address'], dict)


def test_shipping_step_choose_address(rf):
    # address_dict = get_address(NEW_ADDRESS, SHIPPING_PREFIX)
    user = TestUser()
    address = Address(**NEW_ADDRESS)
    address.id = 42
    user.addresses = [address]
    request = rf.post('/checkout/', {'shipping-address-address': '42'})
    request.user = user
    request.session = {STORAGE_SESSION_KEY: {}}
    storage = {}
    step = ShippingAddressStep(request, storage, checkout=MagicMock())
    print repr(step.forms['addresses_form'].is_valid())
    print repr(step.forms['addresses_form'])
    print repr(step.forms['addresses_form'].errors)
    assert step.forms_are_valid()
    step.save()
    assert isinstance(storage['address'. dict])
    assert storage['address_id'] == 42


def test_shipping_step_save_with_address_in_group(rf):
    data = dict(NEW_ADDRESS, method='dummy_shipping')
    request = rf.post('/checkout/', data)
    request.user = AnonymousUser()
    request.session = {}
    # group = MagicMock()
    # group.address = NEW_ADDRESS.copy()
    storage = {'address': NEW_ADDRESS.copy()}
    step = ShippingAddressStep(request, storage)
    assert step.forms_are_valid()
    step.save()
    assert storage['address'] == NEW_ADDRESS


def test_shipping_step_save_with_address_in_checkout(rf):
    data = dict(NEW_ADDRESS, method='dummy_shipping')
    request = rf.post('/checkout/', data)
    request.user = AnonymousUser()
    request.session = {}
    # group = MagicMock()
    # group.address = None
    storage = {
        'address': {
            'first_name': 'Change',
            'last_name': 'Me',
            'id': 10}}
    step = ShippingAddressStep(request, storage)
    assert step.forms_are_valid()
    step.save()
    assert storage['address'] == NEW_ADDRESS


def test_shipping_step_save_with_address_other_than_billing(rf):
    address_data = {
        'first_name': 'Billing Company LTD',
        'last_name': 'Test',
        'street_address_1': 'Test',
        'street_address_2': 'Test',
        'city': 'Test',
        'phone': '12345678',
        'postal_code': '987654',
        'country': 'PL',
        'country_area': '',
        'company_name': 'Test'}
    data = dict(
        address_data,
        method='dummy_shipping',
        shipping_same_as_billing=False)

    request = rf.post('/checkout/', data)
    request.user = AnonymousUser()
    request.session = {}
    group = MagicMock()
    group.address = None
    storage = {
        'address': {
            'first_name': 'Billing Address',
            'last_name': 'Test',
            'id': 10}}
    # billing_address = Address(**address_data)
    step = ShippingAddressStep(request, storage)
    assert step.forms_are_valid()
    step.save()
    assert storage['address'] == address_data


def test_shipping_step_save_same_as_billing(rf):
    address_data = {
        'first_name': 'Billing Company LTD',
        'last_name': 'Test',
        'street_address_1': 'Test',
        'street_address_2': 'Test',
        'city': 'Test',
        'phone': '12345678',
        'postal_code': '987654',
        'country': 'PL',
        'country_area': '',
        'company_name': 'Test'}
    data = dict(
        address_data,
        method='dummy_shipping',
        shipping_same_as_billing=True)

    request = rf.post('/checkout/', data)
    request.user = AnonymousUser()
    request.session = {}
    group = MagicMock()
    group.address = None
    storage = {
        'address': NEW_ADDRESS}
    step = ShippingAddressStep(request, storage, group,
                        billing_address=Address(**NEW_ADDRESS))
    assert step.forms_are_valid()
    step.save()
    assert storage['address'] == NEW_ADDRESS

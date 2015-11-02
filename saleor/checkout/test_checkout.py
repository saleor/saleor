from django.contrib.auth.models import AnonymousUser
from mock import MagicMock

from ..checkout.core import STORAGE_SESSION_KEY
from ..checkout.steps import BaseAddressStep, BillingAddressStep, ShippingStep
from ..userprofile.models import Address

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


def test_base_address_step_works(rf):
    request = rf.post('/checkout/', NEW_ADDRESS)
    request.user = AnonymousUser()
    address = Address(**NEW_ADDRESS)
    step = BaseAddressStep(request, storage={}, address=address)
    assert step.forms_are_valid()
    assert step.address.first_name == 'Test'


def test_billing_address_save_without_address(rf):
    data = dict(NEW_ADDRESS, email='test@example.com')
    request = rf.post('/checkout/', data)
    request.user = AnonymousUser()
    storage = {}
    step = BillingAddressStep(request, storage)
    assert step.process() is None
    assert isinstance(storage['address'], dict)
    assert storage['address']['first_name'] == 'Test'


def test_billing_address_save_with_address_in_checkout(rf):
    data = dict(NEW_ADDRESS, email='test@example.com')
    request = rf.post('/checkout/', data)
    request.user = AnonymousUser()
    storage = {'address': {}}
    step = BillingAddressStep(request, storage)
    assert step.forms_are_valid()


def test_shipping_step_save_without_address(rf):
    data = dict(NEW_ADDRESS, method='dummy_shipping')
    request = rf.post('/checkout/', data)
    request.user = AnonymousUser()
    request.session = {STORAGE_SESSION_KEY: {}}
    group = MagicMock()
    group.address = None
    storage = {'address': NEW_ADDRESS.copy()}
    step = ShippingAddressStep(request, storage, group)
    assert step.forms_are_valid()
    step.save()
    assert isinstance(storage['address'], dict)


def test_shipping_step_save_with_address_in_group(rf):
    data = dict(NEW_ADDRESS, method='dummy_shipping')
    request = rf.post('/checkout/', data)
    request.user = AnonymousUser()
    request.session = {}
    group = MagicMock()
    group.address = NEW_ADDRESS.copy()
    storage = {'address': NEW_ADDRESS.copy()}
    step = ShippingAddressStep(request, storage, group)
    assert step.forms_are_valid()
    step.save()
    assert storage['address'] == NEW_ADDRESS


def test_shipping_step_save_with_address_in_checkout(rf):
    data = dict(NEW_ADDRESS, method='dummy_shipping')
    request = rf.post('/checkout/', data)
    request.user = AnonymousUser()
    request.session = {}
    group = MagicMock()
    group.address = None
    storage = {
        'address': {
            'first_name': 'Change',
            'last_name': 'Me',
            'id': 10}}
    step = ShippingAddressStep(request, storage, group)
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
    billing_address = Address(**address_data)
    step = ShippingAddressStep(request, storage, group, billing_address)
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

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from mock import MagicMock, patch

from . import BillingAddressStep, ShippingStep
from ..checkout import STORAGE_SESSION_KEY
from ..checkout.steps import BaseAddressStep
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
    step = ShippingStep(request, storage, group)
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
    step = ShippingStep(request, storage, group)
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
    step = ShippingStep(request, storage, group)
    assert step.forms_are_valid()
    step.save()
    assert storage['address'] == NEW_ADDRESS

from django.test import TestCase
from mock import MagicMock, patch

from . import BillingAddressStep, ShippingStep
from ..checkout import Checkout, STORAGE_SESSION_KEY
from ..checkout.steps import BaseAddressStep
from ..userprofile.models import Address

NEW_ADDRESS = {
    'name': 'Test',
    'street_address': 'Test',
    'city': 'Test',
    'phone': '12345678',
    'postal_code': '987654',
    'country': 'PL'
}


class TestBaseAddressStep(TestCase):

    def test_new_method(self):
        '''
        Test the BaseAddressStep managment form when method is set to 'new'
        and user isn't authenticated.
        '''
        request = MagicMock()
        request.user.is_authenticated.return_value = False
        request.POST = NEW_ADDRESS.copy()
        step = BaseAddressStep(request, {}, Address(**NEW_ADDRESS))
        self.assertTrue(step.forms_are_valid(), "Forms don't validate.")
        self.assertEqual(step.address.name, 'Test')


class TestBillingAddressStep(TestCase):

    def test_address_save_without_address(self):
        request = MagicMock()
        request.user.is_authenticated.return_value = False
        request.POST = dict(NEW_ADDRESS, email='test@example.com')
        storage = {}
        step = BillingAddressStep(request, storage)
        self.assertEquals(step.process(), None)
        self.assertEqual(type(storage['address']), dict)
        self.assertEqual(storage['address']['name'], 'Test')

    def test_address_save_with_address_in_checkout(self):
        request = MagicMock()
        request.user.is_authenticated.return_value = False
        request.POST = dict(NEW_ADDRESS, email='test@example.com')
        storage = {'address': {}}
        step = BillingAddressStep(request, storage)
        self.assertTrue(step.forms_are_valid(), "Forms don't validate.")


class TestShippingStep(TestCase):

    @patch.object(Address, 'save')
    def test_address_save_without_address(self, mock_save):
        request = MagicMock()
        request.user.is_authenticated.return_value = False
        request.session = {}
        request.POST = dict(NEW_ADDRESS, method='dummy_shipping')
        request.session = {STORAGE_SESSION_KEY: {}}
        group = MagicMock()
        group.address = None
        storage = {'address': NEW_ADDRESS}
        step = ShippingStep(request, storage, group)
        self.assertTrue(step.forms_are_valid(), "Forms don't validate.")
        step.save()
        self.assertEqual(mock_save.call_count, 0)
        self.assertTrue(isinstance(storage['address'], dict),
                        'dict expected')

    @patch.object(Address, 'save')
    def test_address_save_with_address_in_group(self, mock_save):
        request = MagicMock()
        request.user.is_authenticated.return_value = False
        request.session = {}
        request.POST = dict(NEW_ADDRESS, method='dummy_shipping')
        group = MagicMock()
        group.address = NEW_ADDRESS
        storage = {'address': NEW_ADDRESS}
        step = ShippingStep(request, storage, group)
        self.assertTrue(step.forms_are_valid(), "Forms don't validate.")
        step.save()
        self.assertEqual(mock_save.call_count, 0)

    @patch.object(Address, 'save')
    def test_address_save_with_address_in_checkout(self, mock_save):
        request = MagicMock()
        request.user.is_authenticated.return_value = False
        request.session = {}
        request.POST = dict(NEW_ADDRESS, method='dummy_shipping')
        original_billing_address = {'name': 'Change Me', 'id': 10}
        group = MagicMock()
        group.address = None
        storage = {'address': original_billing_address}
        step = ShippingStep(request, storage, group)
        self.assertTrue(step.forms_are_valid(), "Forms don't validate.")
        step.save()
        self.assertEqual(mock_save.call_count, 0)
        self.assertEqual(storage['address'], NEW_ADDRESS)

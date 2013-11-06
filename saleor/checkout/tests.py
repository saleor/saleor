from django.test import TestCase
from mock import MagicMock, patch

from . import BillingAddressStep, ShippingStep
from ..checkout import Checkout
from ..checkout.steps import BaseAddressStep
from ..delivery import DummyShipping
from ..userprofile.models import Address

NEW_ADDRESS = {
    'first_name': 'Test',
    'last_name': 'Test',
    'street_address_1': 'Test',
    'city': 'Test',
    'postal_code': '987654',
    'country': 'PL'}


class TestBaseAddressStep(TestCase):

    def setUp(self):
        self.request = MagicMock()
        self.request.user.is_authenticated.return_value = False
        self.checkout = MagicMock()
        self.address = Address()

    def test_new_method(self):
        '''
        Test the BaseAddressStep managment form when method is set to 'new'
        and user isn't authenticated.
        '''
        self.request.POST = NEW_ADDRESS
        step = BaseAddressStep(self.checkout, self.request, self.address)
        self.assertTrue(step.forms_are_valid(), 'Forms don\'t validate.')
        self.assertEqual(step.address.first_name, 'Test')


class TestBillingAddressStep(TestCase):

    def setUp(self):
        self.request = MagicMock()
        self.request.user.is_authenticated.return_value = False
        self.checkout = MagicMock()

    def test_address_save_without_address(self):
        self.checkout.billing_address = None
        self.request.POST = NEW_ADDRESS
        step = BillingAddressStep(self.checkout, self.request)
        self.assertEquals(step.process(), None)
        self.checkout.save.assert_called_once_with()
        self.assertEqual(type(self.checkout.billing_address), Address)
        self.assertEqual(self.checkout.billing_address.first_name, 'Test')

    def test_address_save_with_address_in_checkout(self):
        self.request.POST = NEW_ADDRESS
        self.request.POST['email'] = 'test@gmail.com'
        self.checkout.billing_address = Address()
        step = BillingAddressStep(self.checkout, self.request)
        self.assertTrue(step.forms_are_valid(), 'Forms don\'t validate.')


class TestShippingStep(TestCase):

    def setUp(self):
        self.request = MagicMock()
        self.request.user.is_authenticated.return_value = False
        self.request.session = {}
        self.checkout = MagicMock()
        self.checkout.get_group.return_value = {}
        self.checkout.billing_address = None

    @patch.object(Address, 'save')
    def test_address_save_without_address(self, mock_save):
        self.request.POST = NEW_ADDRESS
        self.request.POST['method'] = 0
        group = MagicMock()
        group.address = None
        checkout = Checkout(self.request)
        group.get_delivery_methods.return_value = [DummyShipping(group)]
        step = ShippingStep(checkout, self.request, group)
        self.assertTrue(step.forms_are_valid(), 'Forms don\'t validate.')
        step.save()
        self.assertEqual(mock_save.call_count, 0)
        grup_storage = checkout.get_group(str(step))
        self.assertEqual(type(grup_storage['address']), Address,
                         'Address instance expected')

    @patch.object(Address, 'save')
    def test_address_save_with_address_in_group(self, mock_save):
        self.request.POST = NEW_ADDRESS
        self.request.POST['method'] = 0
        group = MagicMock()
        group.address = Address()
        group.get_delivery_methods.return_value = [DummyShipping(group)]
        step = ShippingStep(self.checkout, self.request, group)
        self.assertTrue(step.forms_are_valid(), 'Forms don\'t validate.')
        step.save()
        self.assertEqual(mock_save.call_count, 0)

    @patch.object(Address, 'save')
    def test_address_save_with_address_in_checkout(self, mock_save):
        self.request.POST = NEW_ADDRESS
        self.request.POST['method'] = 0
        original_billing_address_data = {'first_name': 'Change',
                                         'last_name': 'Me',
                                         'id': 10}
        original_billing_address = Address(**original_billing_address_data)
        self.checkout.billing_address = original_billing_address
        group = MagicMock()
        group.address = None
        group.get_delivery_methods.return_value = [DummyShipping(group)]
        step = ShippingStep(self.checkout, self.request, group)
        self.assertTrue(step.forms_are_valid(), 'Forms don\'t validate.')
        step.save()
        self.assertEqual(mock_save.call_count, 0)
        self.assertEqual(self.checkout.billing_address,
                         Address(**original_billing_address_data))
        self.assertEqual(step.group['address'].id, None)

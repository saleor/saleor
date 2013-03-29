from ..steps import BaseShippingStep, BillingAddressStep, ShippingStep
from checkout import Checkout
from delivery import DummyShipping
from django.test import TestCase
from mock import MagicMock
from userprofile.models import Address

NEW_ADDRESS = {
    'first_name': 'Test',
    'last_name': 'Test',
    'street_address_1': 'Test',
    'city': 'Test',
    'postal_code': '987654',
    'country': 'PL'}


NEW_ADDRESS_POST = NEW_ADDRESS.copy()
NEW_ADDRESS_POST['choice_method'] = 'new'


SELECT_ADDRESS_POST = {
    'choice_method': 'select',
    'address': '1'}


class TestBaseShippingStep(TestCase):

    def setUp(self):
        self.request = MagicMock()
        self.request.user.is_authenticated.return_value = False
        self.checkout = MagicMock()
        self.address = Address()

    def test_new_method(self):
        '''
        Test the BaseShippingStep managment form when method is set to 'new'
        and user isn't authenticated.
        '''
        self.request.POST = NEW_ADDRESS_POST
        step = BaseShippingStep(self.checkout, self.request, self.address)
        self.assertTrue(step.forms_are_valid(), 'Forms don\'t validate.')
        self.assertEqual(step.address.first_name, 'Test')

    def test_select_method(self):
        '''
        Test the BaseShippingStep managment form when method is set to 'select'
        and user isn't authenticated.
        '''
        self.request.POST = SELECT_ADDRESS_POST
        step = BaseShippingStep(self.checkout, self.request, self.address)
        self.assertFalse(step.forms_are_valid(), 'Forms should not validate.')

    def test_select_with_user_method(self):
        '''
        Test the BaseShippingStep managment form when method is set to 'select'
        and user is authenticated.
        '''
        user = self.request.user
        self.request.POST = SELECT_ADDRESS_POST
        user.is_authenticated.return_value = True
        user.address_book.all.__iter__.return_value = [self.address]
        step = BaseShippingStep(self.checkout, self.request, self.address)
        self.assertTrue(step.forms_are_valid(), 'Forms don\'t validate.')


class TestBillingAddressStep(TestCase):

    def setUp(self):
        self.request = MagicMock()
        self.request.user.is_authenticated.return_value = False
        self.checkout = MagicMock()

    def test_address_save_without_address(self):
        self.checkout.billing_address = None
        self.request.POST = NEW_ADDRESS_POST
        step = BillingAddressStep(self.checkout, self.request)
        self.assertEquals(step.process(), None)
        self.checkout.save.assert_called_once_with()
        self.assertEqual(type(self.checkout.billing_address), Address)
        self.assertEqual(self.checkout.billing_address.first_name, 'Test')
        step.save()
        self.assertEqual(Address.objects.count(), 0,
                         'No addresses in database expected')

    def test_address_save_with_address_in_checkout(self):
        self.request.POST = NEW_ADDRESS_POST
        self.checkout.billing_address = Address()
        step = BillingAddressStep(self.checkout, self.request)
        self.assertTrue(step.forms_are_valid(), 'Forms don\'t validate.')
        step.save()
        self.assertEqual(Address.objects.count(), 0,
                         'No addresses in database expected')


class TestShippingStep(TestCase):

    def setUp(self):
        self.request = MagicMock()
        self.request.user.is_authenticated.return_value = False
        self.request.session = {}
        self.checkout = MagicMock()
        self.checkout.billing_address = None

    def test_address_save_without_address(self):
        self.request.POST = NEW_ADDRESS_POST
        self.request.POST['method'] = 0
        group = MagicMock()
        group.address = None
        checkout = Checkout(self.request)
        group.get_delivery_methods.return_value = [DummyShipping(group)]
        step = ShippingStep(checkout, self.request, group)
        self.assertTrue(step.forms_are_valid(), 'Forms don\'t validate.')
        self.assertFalse(Address.objects.exists(), 'Init and form validator '
                         'cant\'n create any Addresses')
        step.save()
        self.assertEqual(Address.objects.count(), 0,
                         'No addresses in database expected')
        grup_storage = checkout.get_group(str(step))
        self.assertEqual(type(grup_storage['address']), Address,
                         'Address instance expected')

    def test_address_save_with_address_in_group(self):
        self.request.POST = NEW_ADDRESS_POST
        self.request.POST['method'] = 0
        group = MagicMock()
        group.address = Address()
        group.get_delivery_methods.return_value = [DummyShipping(group)]
        step = ShippingStep(self.checkout, self.request, group)
        self.assertTrue(step.forms_are_valid(), 'Forms don\'t validate.')
        step.save()
        self.assertEqual(Address.objects.count(), 0,
                         'No addresses in database expected')

    def test_address_save_with_address_in_checkout(self):
        self.request.POST = NEW_ADDRESS_POST
        self.request.POST['method'] = 0
        self.checkout.billing_address = Address()
        group = MagicMock()
        group.address = None
        group.get_delivery_methods.return_value = [DummyShipping(group)]
        step = ShippingStep(self.checkout, self.request, group)
        self.assertTrue(step.forms_are_valid(), 'Forms don\'t validate.')
        step.save()
        self.assertEqual(Address.objects.count(), 0,
                         'No addresses in database expected')

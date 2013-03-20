from ..steps import BaseShippingStep, BillingAddressStep
from django.test import TestCase
from mock import MagicMock
from userprofile.models import Address


class TestBaseShippingStep(TestCase):

    def setUp(self):
        self.request = MagicMock()
        self.request.user.is_authenticated.return_value = False
        self.order = MagicMock()
        self.address = MagicMock()
        self.address.id = 1
        self.address.__unicode__.return_value = u'Test'

    def test_new_method(self):
        '''
        Test the BaseShippingStep managment form when method is set to 'new'
        and user isn't authenticated.
        '''
        self.request.POST = {
            'choice_method':'new',
            'first_name': 'Test',
            'last_name': 'Test',
            'street_address_1': 'Test',
            'city': 'Test',
            'postal_code': '987654',
            'country': 'PL'}
        step = BaseShippingStep(self.order, self.request, self.address)
        self.assertTrue(step.forms_are_valid(), 'Forms don\'t validate.')

    def test_select_method(self):
        '''
        Test the BaseShippingStep managment form when method is set to 'select'
        and user isn't authenticated.
        '''
        self.request.POST = {
            'choice_method':'select',
            'address': '1'}
        step = BaseShippingStep(self.order, self.request, self.address)
        self.assertFalse(step.forms_are_valid(), 'Forms should not validate.')

    def test_select_with_user_method(self):
        '''
        Test the BaseShippingStep managment form when method is set to 'select'
        and user is authenticated.
        '''
        user = self.request.user
        self.request.POST = {
            'choice_method':'select',
            'address': '1'}
        user.is_authenticated.return_value = True
        user.address_book.all.__iter__.return_value = [self.address]
        step = BaseShippingStep(self.order, self.request, self.address)
        self.assertTrue(step.forms_are_valid(), 'Forms don\'t validate.')


class TestBillingAddressStep(TestCase):

    def setUp(self):
        self.request = MagicMock()
        self.request.user.is_authenticated.return_value = False
        self.order = MagicMock()
        self.order.billing_address = None

    def test_address_save(self):
        self.request.POST = {
            'choice_method':'new',
            'first_name': 'Test',
            'last_name': 'Test',
            'street_address_1': 'Test',
            'city': 'Test',
            'postal_code': '987654',
            'country': 'PL'}
        step = BillingAddressStep(self.order, self.request)
        self.assertEquals(step.process(), None)
        self.order.save.assert_called_once_with()
        self.assertEqual(type(self.order.billing_address), Address)
        self.assertEqual(self.order.billing_address.first_name, 'Test')


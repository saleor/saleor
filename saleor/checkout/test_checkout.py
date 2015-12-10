from django.contrib.auth.models import AnonymousUser
from mock import MagicMock, patch
from satchless.process import InvalidData

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

        def get(self, pk):
            pk = int(pk)
            for address in TestUser._addresses:
                if address.id == pk:
                    return address

    _addresses = QuerysetMock()
    _email = 'user@example.com'

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

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        pass


def get_address(address, prefix=''):
    if prefix:
        prefix = '%s-' % (prefix,)

    return {prefix + k: v for k, v in address.items()}


def test_shipping_step_save_address_anonymous_user(rf):
    address = get_address(NEW_ADDRESS, SHIPPING_PREFIX)
    data = dict(address, email=USER_EMAIL)
    data[SHIPPING_PREFIX + '-address'] = 'new'
    request = rf.post('/checkout/', data)
    request.user = AnonymousUser()
    request.session = {STORAGE_SESSION_KEY: {}}
    storage = {}
    step = ShippingAddressStep(request, storage, checkout=MagicMock())
    assert step.forms_are_valid()
    step.save()
    assert isinstance(storage['address'], dict)
    assert storage['email'] == USER_EMAIL
    try:
        step.validate()
    except InvalidData:
        is_valid = False
    else:
        is_valid = True
    assert is_valid is True


def test_shipping_step_address_without_email_anonymous_user(rf):
    address = get_address(NEW_ADDRESS, SHIPPING_PREFIX)
    address[SHIPPING_PREFIX + '-address'] = 'new'
    request = rf.post('/checkout/', address)
    request.user = AnonymousUser()
    request.session = {STORAGE_SESSION_KEY: {}}
    storage = {}
    step = ShippingAddressStep(request, storage, checkout=MagicMock())
    assert not step.forms_are_valid()


def test_shipping_step_without_address_anonymous_user(rf):
    request = rf.post('/checkout/', {'email': USER_EMAIL})
    request.user = AnonymousUser()
    request.session = {STORAGE_SESSION_KEY: {}}
    storage = {}
    step = ShippingAddressStep(request, storage, checkout=MagicMock())
    assert not step.forms_are_valid()


def test_shipping_step_save_address_authenticated_user(rf):
    address = get_address(NEW_ADDRESS, SHIPPING_PREFIX)
    address[SHIPPING_PREFIX + '-address'] = 'new'
    user = TestUser()
    request = rf.post('/checkout/', address)
    request.user = user
    request.session = {STORAGE_SESSION_KEY: {}}
    storage = {}
    step = ShippingAddressStep(request, storage, checkout=MagicMock())
    assert step.forms_are_valid()
    step.save()
    assert isinstance(storage['address'], dict)
    try:
        step.validate()
    except InvalidData:
        is_valid = False
    else:
        is_valid = True
    assert is_valid is True


def test_shipping_step_choose_own_address(rf):
    user = TestUser()
    address = Address(**NEW_ADDRESS)
    address.id = 42
    user.addresses = [address]
    request = rf.post('/checkout/', {SHIPPING_PREFIX + '-address': '42'})
    request.user = user
    request.session = {STORAGE_SESSION_KEY: {}}
    storage = {}
    step = ShippingAddressStep(request, storage, checkout=MagicMock())
    assert step.forms_are_valid()
    step.save()
    assert isinstance(storage['address'], dict)
    assert storage['address_id'] == 42
    try:
        step.validate()
    except InvalidData:
        is_valid = False
    else:
        is_valid = True
    assert is_valid is True


def test_shipping_step_save_address_reload_step(rf):
    saved_address_data = NEW_ADDRESS
    new_address_data = dict(NEW_ADDRESS, first_name='Another address')
    new_address_form = get_address(new_address_data, SHIPPING_PREFIX)
    new_address_form[SHIPPING_PREFIX + '-address'] = 'new'
    request = rf.post('/checkout/', new_address_form)
    request.user = TestUser()
    request.session = {STORAGE_SESSION_KEY: {}}
    storage = {'address': saved_address_data}
    step = ShippingAddressStep(request, storage, checkout=MagicMock())
    previous_address = Address(**saved_address_data)
    saved_address = Address(**step.storage['address'])
    assert Address.objects.are_identical(previous_address, saved_address)
    step.forms_are_valid()
    step.save()
    new_saved_address = Address(**step.storage['address'])
    new_provided_address = Address(**new_address_data)
    assert Address.objects.are_identical(new_saved_address,
                                         new_provided_address)
    try:
        step.validate()
    except InvalidData:
        is_valid = False
    else:
        is_valid = True
    assert is_valid is True


def test_shipping_step_provide_false_address(rf):
    user = TestUser()
    address = Address(**NEW_ADDRESS)
    address.id = 42
    user.addresses = [address]
    request = rf.post('/checkout/', {SHIPPING_PREFIX + '-address': '13'})
    request.user = user
    request.session = {STORAGE_SESSION_KEY: {}}
    storage = {}
    step = ShippingAddressStep(request, storage, checkout=MagicMock())
    assert not step.forms_are_valid()


def test_shipping_method_step(rf):
    shipping_method_name = 'a_shipping_method'
    request = rf.post('/shipping-method/', {'method': shipping_method_name})
    request.session = {STORAGE_SESSION_KEY: {}}
    storage = {}
    shipping_method = MagicMock()
    shipping_method.get_delivery_total = MagicMock()
    shipping_method.get_delivery_total.return_value = 7
    shipping_method.name = shipping_method_name

    with patch('saleor.checkout.steps.get_delivery_options_for_items') as (
            shipping_options):
        shipping_options.return_value = [shipping_method]
        step = ShippingMethodStep(
            request, storage, shipping_address=MagicMock(), cart=MagicMock(),
            checkout=MagicMock())
    assert step.forms_are_valid()
    step.save()
    assert step.storage['shipping_method'] == shipping_method_name
    try:
        step.validate()
    except InvalidData:
        is_valid = False
    else:
        is_valid = True
    assert is_valid is True


def test_shipping_method_reload_step(rf):
    new_shipping_method_name = 'another_shipping_method'
    request = rf.post('/shipping-method/',
                      {'method': new_shipping_method_name})
    request.session = {STORAGE_SESSION_KEY: {}}
    shipping_method = MagicMock()
    shipping_method.get_delivery_total = MagicMock()
    shipping_method.get_delivery_total.return_value = 7
    shipping_method.name = new_shipping_method_name

    with patch('saleor.checkout.steps.get_delivery_options_for_items') as (
            shipping_options):
        storage = {'shipping_method': 'previous_shipping_method'}
        shipping_options.return_value = [shipping_method]
        step = ShippingMethodStep(
            request, storage, shipping_address=MagicMock(), cart=MagicMock(),
            checkout=MagicMock())
    assert step.storage['shipping_method'] == 'previous_shipping_method'
    assert step.forms_are_valid()
    step.save()
    assert step.storage['shipping_method'] == new_shipping_method_name
    try:
        step.validate()
    except InvalidData:
        is_valid = False
    else:
        is_valid = True
    assert is_valid is True


def test_false_shipping_method_step(rf):
    request = rf.post('/shipping-method/', {'method': 'bad_shipping_method'})
    request.session = {STORAGE_SESSION_KEY: {}}
    storage = {}
    shipping_method = MagicMock()
    shipping_method.get_delivery_total = MagicMock()
    shipping_method.get_delivery_total.return_value = 7
    shipping_method.name = 'a_shipping_method'

    with patch('saleor.checkout.steps.get_delivery_options_for_items') as (
            shipping_options):
        shipping_options.return_value = [shipping_method]
        step = ShippingMethodStep(
            request, storage, shipping_address=MagicMock(), cart=MagicMock(),
            checkout=MagicMock())
    assert not step.forms_are_valid()


def test_billing_step_copy_shipping_address(rf):
    shipping_address = Address(**NEW_ADDRESS)
    request = rf.post('/summary/', {'summary-address': 'copy'})
    request.user = AnonymousUser()
    request.session = {STORAGE_SESSION_KEY: {}}
    storage = {}
    checkout = MagicMock()
    checkout.is_shipping_required = MagicMock()
    checkout.is_shipping_required.return_value = True
    step = SummaryStep(request, storage, shipping_address, checkout)
    assert step.forms_are_valid()
    step.save()
    saved_address = Address(**step.storage['billing_address'])
    assert Address.objects.are_identical(shipping_address, saved_address)


def test_billing_step_save_new_address(rf):
    shipping_address = Address(**NEW_ADDRESS)
    billing_address_data = dict(NEW_ADDRESS, first_name='Another address')
    data = get_address(billing_address_data, SUMMARY_PREFIX)
    data['summary-address'] = 'new'
    request = rf.post('/summary/', data)
    request.user = AnonymousUser()
    request.session = {STORAGE_SESSION_KEY: {}}
    storage = {}
    checkout = MagicMock()
    checkout.is_shipping_required = MagicMock()
    checkout.is_shipping_required.return_value = True
    step = SummaryStep(request, storage, shipping_address, checkout)
    assert step.forms_are_valid()
    step.save()
    saved_address = Address(**step.storage['billing_address'])
    billing_address = Address(**billing_address_data)
    assert Address.objects.are_identical(billing_address, saved_address)


def test_billing_step_choose_own_address(rf):
    shipping_address = Address(**NEW_ADDRESS)
    billing_address_data = dict(NEW_ADDRESS, first_name='Another address')
    user = TestUser()
    billing_address = Address(**billing_address_data)
    billing_address.id = 13
    user.addresses = [billing_address]
    request = rf.post('/summary/', {'summary-address': '13'})
    request.user = user
    request.session = {STORAGE_SESSION_KEY: {}}
    storage = {}
    checkout = MagicMock()
    checkout.is_shipping_required = MagicMock()
    checkout.is_shipping_required.return_value = True
    step = SummaryStep(request, storage, shipping_address, checkout)
    assert step.forms_are_valid()
    step.save()
    saved_address = Address(**step.storage['billing_address'])
    assert Address.objects.are_identical(billing_address, saved_address)


def test_billing_step_provide_false_address(rf):
    shipping_address = Address(**NEW_ADDRESS)
    billing_address_data = dict(NEW_ADDRESS, first_name='Another address')
    user = TestUser()
    billing_address = Address(**billing_address_data)
    billing_address.id = 13
    user.addresses = [billing_address]
    request = rf.post('/summary/', {'summary-address': '69'})
    request.user = user
    request.session = {STORAGE_SESSION_KEY: {}}
    storage = {}
    checkout = MagicMock()
    checkout.is_shipping_required = MagicMock()
    checkout.is_shipping_required.return_value = True
    step = SummaryStep(request, storage, shipping_address, checkout)
    assert not step.forms_are_valid()


def test_billing_step_save_address_anonymous_user_without_shipping(rf):
    data = get_address(NEW_ADDRESS, SUMMARY_PREFIX)
    data['summary-address'] = 'new'
    data['email'] = USER_EMAIL
    request = rf.post('/summary/', data)
    request.user = AnonymousUser()
    request.session = {STORAGE_SESSION_KEY: {}}
    storage = {}
    checkout = MagicMock()
    checkout.is_shipping_required = MagicMock()
    checkout.is_shipping_required.return_value = False
    step = SummaryStep(request, storage, shipping_address=None,
                       checkout=checkout)
    assert step.forms_are_valid()
    step.save()
    saved_address = Address(**step.storage['billing_address'])
    billing_address = Address(**NEW_ADDRESS)
    assert Address.objects.are_identical(billing_address, saved_address)
    assert step.storage['email'] == USER_EMAIL


def test_billing_step_anonymous_user_without_address_without_shipping(rf):
    data = {'summary-address': 'new', 'email': USER_EMAIL}
    request = rf.post('/summary/', data)
    request.user = AnonymousUser()
    request.session = {STORAGE_SESSION_KEY: {}}
    storage = {}
    checkout = MagicMock()
    checkout.is_shipping_required = MagicMock()
    checkout.is_shipping_required.return_value = False
    step = SummaryStep(request, storage, shipping_address=None,
                       checkout=checkout)
    assert not step.forms_are_valid()


def test_billing_step_anonymous_user_without_email_without_shipping(rf):
    data = get_address(NEW_ADDRESS, SUMMARY_PREFIX)
    data['summary-address'] = 'new'
    request = rf.post('/summary/', data)
    request.user = AnonymousUser()
    request.session = {STORAGE_SESSION_KEY: {}}
    storage = {}
    checkout = MagicMock()
    checkout.is_shipping_required = MagicMock()
    checkout.is_shipping_required.return_value = False
    step = SummaryStep(request, storage, shipping_address=None,
                       checkout=checkout)
    assert not step.forms_are_valid()

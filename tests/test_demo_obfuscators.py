from django.conf import settings
from phonenumber_field.phonenumber import PhoneNumber

from saleor.core.utils import random_data
from saleor.core.templatetags.demo_obfuscators import (
    obfuscate_address, obfuscate_email, obfuscate_phone, obfuscate_string)
from saleor.userprofile.models import User


def test_obfuscate_address():
    address = random_data.create_address()
    obfuscated_address = obfuscate_address(address)

    assert obfuscated_address != address
    assert obfuscated_address.pk is None
    assert obfuscated_address.street_address_2 == ''

    assert obfuscated_address.street_address_1 != address.street_address_1
    assert obfuscated_address.city != address.city
    assert obfuscated_address.postal_code != address.postal_code

    assert obfuscated_address.first_name == address.first_name
    assert obfuscated_address.last_name == address.last_name
    assert obfuscated_address.country == address.country

    assert obfuscated_address.street_address_1 == obfuscate_string(
        address.street_address_1)
    assert obfuscated_address.city == obfuscate_string(address.city)
    assert obfuscated_address.postal_code == obfuscate_string(
        address.postal_code)


def test_obfuscate_email():
    assert obfuscate_email('t@mail.dev') == 't...@example.com'
    assert obfuscate_email('test@mail.dev') == 'tes...@example.com'
    assert obfuscate_email('test@invalid@mail.dev') == 'tes...@example.com'
    assert obfuscate_email(User(email='test@mail.dev')) == 'tes...@example.com'

    assert obfuscate_email('') == obfuscate_string('')
    assert obfuscate_email('t') == obfuscate_string('t')
    assert obfuscate_email('test') == obfuscate_string('test')

    assert obfuscate_email(
        settings.DEMO_ADMIN_EMAIL) == settings.DEMO_ADMIN_EMAIL


def test_obfuscate_phone():
    assert obfuscate_phone(
        PhoneNumber.from_string('+447446844846')) == '+44...46'

    assert obfuscate_phone('') == ''
    assert obfuscate_phone('abcd') == 'abc...'


def test_obfuscate_string():
    assert obfuscate_string('') == ''
    assert obfuscate_string('t') == 't...'
    assert obfuscate_string('test') == 'tes...'
    assert obfuscate_string('loremi') == 'lor...'
    assert obfuscate_string('loremip') == 'lor...p'
    assert obfuscate_string('loremipsum') == 'lor...sum'
    assert obfuscate_string(User(email='test@example.com')) == 'tes...com'

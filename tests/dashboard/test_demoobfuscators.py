from phonenumber_field.phonenumber import PhoneNumber

from saleor.dashboard.templatetags.demoobfuscators import (
    obfuscate_email, obfuscate_phone, obfuscate_string)
from saleor.userprofile.models import User


def test_obfuscate_email():
    assert obfuscate_email('t@mail.dev') == 't...@example.com'
    assert obfuscate_email('test@mail.dev') == 'tes...@example.com'
    assert obfuscate_email('test@invalid@mail.dev') == 'tes...@example.com'
    assert obfuscate_email(User(email='test@mail.dev')) == 'tes...@example.com'

    assert obfuscate_email('') == obfuscate_string('')
    assert obfuscate_email('t') == obfuscate_string('t')
    assert obfuscate_email('test') == obfuscate_string('test')


def test_obfuscate_phone():
    assert obfuscate_phone(
        PhoneNumber.from_string('+447446844846')) == '+44...'

    assert obfuscate_phone('') == ''
    assert obfuscate_phone('abcd') == 'abc...'


def test_obfuscate_string():
    assert obfuscate_string('') == ''
    assert obfuscate_string('t') == 't...'
    assert obfuscate_string('test') == 'tes...'
    assert obfuscate_string(User(email='test@example.com')) == 'tes...'

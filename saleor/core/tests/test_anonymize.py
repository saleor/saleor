from ..anonymize import obfuscate_address, obfuscate_email, obfuscate_string


def test_obfuscate_email():
    # given
    email = "abc@gmail.com"

    # when
    result = obfuscate_email(email)

    # then
    assert result == "a...@gmail.com"


def test_obfuscate_email_example_email():
    # given
    email = "abc@example.com"

    # when
    result = obfuscate_email(email)

    # then
    assert result == "a...@example.com"


def test_obfuscate_email_no_at_in_email():
    # given
    email = "abcgmail.com"

    # when
    result = obfuscate_email(email)

    # then
    assert result == "a..........."


def test_obfuscate_string():
    # given
    value = "AbcDef"

    # when
    result = obfuscate_string(value)

    # then
    assert result == "A....."


def test_obfuscate_string_empty_string():
    # given
    value = ""

    # when
    result = obfuscate_string(value)

    # then
    assert result == value


def test_obfuscate_string_phone_string():
    # given
    value = "+40123123123"

    # when
    result = obfuscate_string(value, phone=True)

    # then
    assert result == "+40........."


def test_obfuscate_address(address):
    # given
    first_name = address.first_name
    last_name = address.last_name
    company_name = address.company_name
    street_address_1 = address.street_address_1
    phone = str(address.phone)

    # when
    result = obfuscate_address(address)

    # then
    assert result.first_name == first_name[0] + "." * (len(first_name) - 1)
    assert result.last_name == last_name[0] + "." * (len(last_name) - 1)
    assert result.company_name == company_name[0] + "." * (len(company_name) - 1)
    assert result.street_address_1 == street_address_1[0] + "." * (
        len(street_address_1) - 1
    )
    assert result.street_address_2 == ""
    assert result.phone == phone[:3] + "." * (len(phone) - 3)


def test_obfuscate_address_no_address(address):
    # when
    result = obfuscate_address(None)

    # then
    assert result is None

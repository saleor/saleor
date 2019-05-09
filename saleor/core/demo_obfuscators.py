from django.conf import settings


def obfuscate_address(address):
    address.first_name = obfuscate_string(address.first_name)
    address.last_name = obfuscate_string(address.last_name)
    address.company_name = obfuscate_string(address.company_name)
    address.street_address_1 = obfuscate_string(address.street_address_1)
    address.street_address_2 = obfuscate_string(address.street_address_2)
    address.city = obfuscate_string(address.city)
    address.postal_code = obfuscate_string(address.postal_code)
    address.save()
    return address


def obfuscate_email(value):
    """
    This filter obfuscates string (or object's __str__() result) with e-mail,
    returning only its first character followed by @example.com hostname.

    We are using naive e-mail validation here, just checking for @'s presence
    in filtered string, and fallback to obfuscate_string() if its not found.

    If value to be obfuscated is same as one defined in the DEMO_ADMIN_EMAIL
    setting, obfuscation will be skipped.
    """
    string_rep = str(value)
    if string_rep == settings.DEMO_ADMIN_EMAIL:
        return string_rep
    if "@" not in str(string_rep):
        return obfuscate_string(string_rep)
    username = str(string_rep).split("@")[0]
    return "%s...@example.com" % str(username)[:3]


def obfuscate_phone(value):
    """
    This filter obfuscates the phonenumber_field.PhoneNumber for printing.

    We fallback to obfuscate_string if value is not valid PhoneNumber or
    compatibile object.
    """
    try:
        if value.country_code and value.national_number:
            return "+%s...%s" % (value.country_code, str(value.national_number)[-2:])
    except AttributeError:
        return obfuscate_string(value)


def obfuscate_string(value):
    """
    This filter obfuscates string (or object's __str__() result), returning
    only first three characters followed by ellipsis. For strings longer
    than 6 we also include trailing part no longer than 3 characters.
    """
    if not value:
        return ""

    string_rep = str(value)
    if len(string_rep) > 6:
        slice_tail = min([3, len(string_rep) - 6]) * -1
        return "%s...%s" % (string_rep[:3], string_rep[slice_tail:])
    return "%s..." % string_rep[:3]


def obfuscate_cart(cart):
    cart.email = obfuscate_email(cart.email)
    if cart.shipping_address:
        cart.shipping_address = obfuscate_address(cart.shipping_address)
    if cart.billing_address:
        cart.billing_address = obfuscate_address(cart.billing_address)
    cart.save()


def obfuscate_order(order):
    order.user_email = obfuscate_email(order.user_email)
    if order.shipping_address:
        order.shipping_address = obfuscate_address(order.shipping_address)
    if order.billing_address:
        order.billing_address = obfuscate_address(order.billing_address)
    order.save()

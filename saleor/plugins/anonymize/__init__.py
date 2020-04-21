def obfuscate_address(address):
    address.first_name = obfuscate_string(address.first_name)
    address.last_name = obfuscate_string(address.last_name)
    address.company_name = obfuscate_string(address.company_name)
    address.street_address_1 = obfuscate_string(address.street_address_1)
    address.street_address_2 = obfuscate_string(address.street_address_2)
    return address


def obfuscate_email(value):
    string_rep = str(value)
    if string_rep.endswith("@example.com"):
        return string_rep
    if "@" not in str(string_rep):
        return obfuscate_string(string_rep)
    username = str(string_rep).split("@")[0]
    return "%s...@example.com" % str(username)[:3]


def obfuscate_string(value):
    if not value:
        return ""

    string_rep = str(value)
    if len(string_rep) > 6:
        slice_tail = min([3, len(string_rep) - 6]) * -1
        return "%s...%s" % (string_rep[:3], string_rep[slice_tail:])
    return "%s..." % string_rep[:3]


def obfuscate_order(order):
    order.user_email = obfuscate_email(order.user_email)
    if order.shipping_address:
        order.shipping_address = obfuscate_address(order.shipping_address)
        order.shipping_address.save()
    if order.billing_address:
        order.billing_address = obfuscate_address(order.billing_address)
        order.billing_address.save()
    return order

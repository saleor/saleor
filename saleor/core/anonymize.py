def obfuscate_email(value):
    string_rep = str(value)
    if string_rep.endswith("@example.com"):
        return string_rep
    if "@" not in str(string_rep):
        return obfuscate_string(string_rep)
    username = str(string_rep).split("@")[0]
    return "%s...@example.com" % str(username)[:1]


def obfuscate_string(value, phone=False):
    if not value:
        return ""

    string_rep = str(value)
    string_len = len(string_rep)
    cutoff = 3 if phone else 1
    return string_rep[:cutoff] + "." * (string_len - cutoff)


def obfuscate_address(address):
    if not address:
        return address
    address.first_name = obfuscate_string(address.first_name)
    address.last_name = obfuscate_string(address.last_name)
    address.company_name = obfuscate_string(address.company_name)
    address.street_address_1 = obfuscate_string(address.street_address_1)
    address.street_address_2 = obfuscate_string(address.street_address_2)
    address.phone = obfuscate_string(address.phone, phone=True)
    return address

from ...core.utils import snake_to_camel_case


def convert_dict_keys_to_camel_case(d):
    """Changes dict fields from d[field_name] to d[fieldName].

    Useful when dealing with dict data such as address that need to be parsed
    into graphql input.
    """
    data = {}
    for k, v in d.items():
        new_key = snake_to_camel_case(k)
        data[new_key] = d[k]
    return data


def get_address_for_search_document(address):
    if isinstance(address, dict):
        address_data = (
            f"{address['firstName']}{address['lastName']}"
            f"{address['streetAddress1']}{address['streetAddress2']}"
            f"{address['city']}{address['postalCode']}"
            f"{address['country']}{address['phone']}"
        )
    else:
        address_data = (
            f"{address.first_name}{address.last_name}"
            f"{address.street_address_1}{address.street_address_2}"
            f"{address.city}{address.postal_code}"
            f"{address.country}{address.phone}"
        )
    return address_data.replace(" ", "").lower()

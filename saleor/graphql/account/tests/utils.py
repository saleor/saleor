from ...core.utils import snake_to_camel_case


def convert_dict_keys_to_camel_case(d):
    """Change dict fields from snake_case to camelCase.

    Useful when dealing with dict data such as address that need to be parsed
    into GraphQL input.
    """
    data = {}
    for k, v in d.items():
        new_key = snake_to_camel_case(k)
        data[new_key] = d[k]
    return data

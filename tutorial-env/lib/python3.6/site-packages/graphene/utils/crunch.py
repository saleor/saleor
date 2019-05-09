import json
from collections import Mapping


def to_key(value):
    return json.dumps(value)


def insert(value, index, values):
    key = to_key(value)

    if key not in index:
        index[key] = len(values)
        values.append(value)
        return len(values) - 1

    return index.get(key)


def flatten(data, index, values):
    if isinstance(data, (list, tuple)):
        flattened = [flatten(child, index, values) for child in data]
    elif isinstance(data, Mapping):
        flattened = {key: flatten(child, index, values) for key, child in data.items()}
    else:
        flattened = data
    return insert(flattened, index, values)


def crunch(data):
    index = {}
    values = []

    flatten(data, index, values)
    return values

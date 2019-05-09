from collections import Mapping, OrderedDict


def deflate(node, index=None, path=None):
    if index is None:
        index = {}
    if path is None:
        path = []

    if node and "id" in node and "__typename" in node:
        route = ",".join(path)
        cache_key = ":".join([route, str(node["__typename"]), str(node["id"])])

        if index.get(cache_key) is True:
            return {"__typename": node["__typename"], "id": node["id"]}
        else:
            index[cache_key] = True

    field_names = node.keys()
    result = OrderedDict()

    for field_name in field_names:
        value = node[field_name]

        new_path = path + [field_name]
        if isinstance(value, (list, tuple)):
            result[field_name] = [deflate(child, index, new_path) for child in value]
        elif isinstance(value, Mapping):
            result[field_name] = deflate(value, index, new_path)
        else:
            result[field_name] = value

    return result

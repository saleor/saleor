class _OldClass:
    pass


class _NewClass(object):
    pass


_all_vars = set(dir(_OldClass) + dir(_NewClass))


def props(x):
    return {
        key: vars(x).get(key, getattr(x, key)) for key in dir(x) if key not in _all_vars
    }

def get_unbound_function(func):
    if not getattr(func, "__self__", True):
        return func.__func__
    return func

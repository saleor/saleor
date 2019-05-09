import importlib


def import_class(path):
    """Import class by path given."""
    path_bits = path.split('.')
    # Cut off the class name at the end.
    class_name = path_bits.pop()
    module_path = '.'.join(path_bits)
    module_itself = importlib.import_module(module_path)

    if not hasattr(module_itself, class_name):
        raise ImportError("The Python module '%s' has no '%s' class."
                          "" % (module_path, class_name))

    return getattr(module_itself, class_name)

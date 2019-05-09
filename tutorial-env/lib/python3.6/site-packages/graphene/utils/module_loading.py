from functools import partial
from importlib import import_module


def import_string(dotted_path, dotted_attributes=None):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. When a dotted attribute path is also provided, the
    dotted attribute path would be applied to the attribute/class retrieved from
    the first step, and return the corresponding value designated by the
    attribute path. Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError:
        raise ImportError("%s doesn't look like a module path" % dotted_path)

    module = import_module(module_path)

    try:
        result = getattr(module, class_name)
    except AttributeError:
        raise ImportError(
            'Module "%s" does not define a "%s" attribute/class'
            % (module_path, class_name)
        )

    if not dotted_attributes:
        return result
    else:
        attributes = dotted_attributes.split(".")
        traveled_attributes = []
        try:
            for attribute in attributes:
                traveled_attributes.append(attribute)
                result = getattr(result, attribute)
            return result
        except AttributeError:
            raise ImportError(
                'Module "%s" does not define a "%s" attribute inside attribute/class "%s"'
                % (module_path, ".".join(traveled_attributes), class_name)
            )


def lazy_import(dotted_path, dotted_attributes=None):
    return partial(import_string, dotted_path, dotted_attributes)

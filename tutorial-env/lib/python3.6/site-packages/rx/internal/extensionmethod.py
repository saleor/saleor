def extensionmethod(base, name=None, decorator=None, instancemethod=False, alias=None):
    """Function decorator that extends base with the decorated
    function.

    Keyword arguments:
    :param T base: Base class to extend with method
    :param string name: Name of method to set
    :param Callable decorator: Additional decorator e.g staticmethod

    :returns: A function that takes the class to be decorated.
    :rtype: func -> func
    """

    def inner(func):
        """This function is returned by the outer extensionmethod()

        :param types.FunctionType func: Function to be decorated
        """

        func_names = [name or func.__name__]
        if alias:
            aliases = alias if isinstance(alias, list) else [alias]
            func_names += aliases

        func = decorator(func) if decorator else func

        for func_name in func_names:
            if instancemethod:
                if hasattr(base, "_methods"):
                    base._methods.append((func_name, func))
                else:
                    base._methods = [(func_name, func)]
            else:
                setattr(base, func_name, func)
        return func
    return inner


def extensionclassmethod(base, name=None, alias=None):
    """Function decorator that extends base with the decorated
    function as a class method.

    Keyword arguments:
    :param T base: Base class to extend with classmethod
    :param string name: Name of method to set

    :returns: A function that takes the class to be decorated.
    :rtype: func -> func
    """

    return extensionmethod(base=base, name=name, decorator=classmethod, alias=alias)

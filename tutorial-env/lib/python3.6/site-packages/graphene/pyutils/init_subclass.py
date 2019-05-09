is_init_subclass_available = hasattr(object, "__init_subclass__")

if not is_init_subclass_available:

    class InitSubclassMeta(type):
        """Metaclass that implements PEP 487 protocol"""

        def __new__(cls, name, bases, ns, **kwargs):
            __init_subclass__ = ns.pop("__init_subclass__", None)
            if __init_subclass__:
                __init_subclass__ = classmethod(__init_subclass__)
                ns["__init_subclass__"] = __init_subclass__
            return super(InitSubclassMeta, cls).__new__(cls, name, bases, ns, **kwargs)

        def __init__(cls, name, bases, ns, **kwargs):
            super(InitSubclassMeta, cls).__init__(name, bases, ns)
            super_class = super(cls, cls)
            if hasattr(super_class, "__init_subclass__"):
                super_class.__init_subclass__.__func__(cls, **kwargs)


else:
    InitSubclassMeta = type  # type: ignore

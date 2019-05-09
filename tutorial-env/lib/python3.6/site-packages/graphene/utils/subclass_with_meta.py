from inspect import isclass

import six

from ..pyutils.init_subclass import InitSubclassMeta
from .props import props


class SubclassWithMeta_Meta(InitSubclassMeta):
    _meta = None

    def __str__(cls):
        if cls._meta:
            return cls._meta.name
        return cls.__name__

    def __repr__(cls):
        return "<{} meta={}>".format(cls.__name__, repr(cls._meta))


class SubclassWithMeta(six.with_metaclass(SubclassWithMeta_Meta)):
    """This class improves __init_subclass__ to receive automatically the options from meta"""

    # We will only have the metaclass in Python 2
    def __init_subclass__(cls, **meta_options):
        """This method just terminates the super() chain"""
        _Meta = getattr(cls, "Meta", None)
        _meta_props = {}
        if _Meta:
            if isinstance(_Meta, dict):
                _meta_props = _Meta
            elif isclass(_Meta):
                _meta_props = props(_Meta)
            else:
                raise Exception(
                    "Meta have to be either a class or a dict. Received {}".format(
                        _Meta
                    )
                )
            delattr(cls, "Meta")
        options = dict(meta_options, **_meta_props)

        abstract = options.pop("abstract", False)
        if abstract:
            assert not options, (
                "Abstract types can only contain the abstract attribute. "
                "Received: abstract, {option_keys}"
            ).format(option_keys=", ".join(options.keys()))
        else:
            super_class = super(cls, cls)
            if hasattr(super_class, "__init_subclass_with_meta__"):
                super_class.__init_subclass_with_meta__(**options)

    @classmethod
    def __init_subclass_with_meta__(cls, **meta_options):
        """This method just terminates the super() chain"""

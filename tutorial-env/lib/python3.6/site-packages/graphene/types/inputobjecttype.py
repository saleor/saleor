from collections import OrderedDict

from .base import BaseOptions, BaseType
from .inputfield import InputField
from .unmountedtype import UnmountedType
from .utils import yank_fields_from_attrs

# For static type checking with Mypy
MYPY = False
if MYPY:
    from typing import Dict, Callable  # NOQA


class InputObjectTypeOptions(BaseOptions):
    fields = None  # type: Dict[str, InputField]
    container = None  # type: InputObjectTypeContainer


class InputObjectTypeContainer(dict, BaseType):
    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        for key in self._meta.fields.keys():
            setattr(self, key, self.get(key, None))

    def __init_subclass__(cls, *args, **kwargs):
        pass


class InputObjectType(UnmountedType, BaseType):
    """
    Input Object Type Definition

    An input object defines a structured collection of fields which may be
    supplied to a field argument.

    Using `NonNull` will ensure that a value must be provided by the query
    """

    @classmethod
    def __init_subclass_with_meta__(cls, container=None, _meta=None, **options):
        if not _meta:
            _meta = InputObjectTypeOptions(cls)

        fields = OrderedDict()
        for base in reversed(cls.__mro__):
            fields.update(yank_fields_from_attrs(base.__dict__, _as=InputField))

        if _meta.fields:
            _meta.fields.update(fields)
        else:
            _meta.fields = fields
        if container is None:
            container = type(cls.__name__, (InputObjectTypeContainer, cls), {})
        _meta.container = container
        super(InputObjectType, cls).__init_subclass_with_meta__(_meta=_meta, **options)

    @classmethod
    def get_type(cls):
        """
        This function is called when the unmounted type (InputObjectType instance)
        is mounted (as a Field, InputField or Argument)
        """
        return cls

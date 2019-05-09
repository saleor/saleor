from ..utils.subclass_with_meta import SubclassWithMeta
from ..utils.trim_docstring import trim_docstring


class BaseOptions(object):
    name = None  # type: str
    description = None  # type: str

    _frozen = False  # type: bool

    def __init__(self, class_type):
        self.class_type = class_type  # type: Type

    def freeze(self):
        self._frozen = True

    def __setattr__(self, name, value):
        if not self._frozen:
            super(BaseOptions, self).__setattr__(name, value)
        else:
            raise Exception("Can't modify frozen Options {}".format(self))

    def __repr__(self):
        return "<{} name={}>".format(self.__class__.__name__, repr(self.name))


class BaseType(SubclassWithMeta):
    @classmethod
    def create_type(cls, class_name, **options):
        return type(class_name, (cls,), {"Meta": options})

    @classmethod
    def __init_subclass_with_meta__(cls, name=None, description=None, _meta=None):
        assert "_meta" not in cls.__dict__, "Can't assign directly meta"
        if not _meta:
            return
        _meta.name = name or cls.__name__
        _meta.description = description or trim_docstring(cls.__doc__)
        _meta.freeze()
        cls._meta = _meta
        super(BaseType, cls).__init_subclass_with_meta__()

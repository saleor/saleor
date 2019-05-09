from .mountedtype import MountedType
from .structures import NonNull
from .utils import get_type


class InputField(MountedType):
    def __init__(
        self,
        type,
        name=None,
        default_value=None,
        deprecation_reason=None,
        description=None,
        required=False,
        _creation_counter=None,
        **extra_args
    ):
        super(InputField, self).__init__(_creation_counter=_creation_counter)
        self.name = name
        if required:
            type = NonNull(type)
        self._type = type
        self.deprecation_reason = deprecation_reason
        self.default_value = default_value
        self.description = description

    @property
    def type(self):
        return get_type(self._type)

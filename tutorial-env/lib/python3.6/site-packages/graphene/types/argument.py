from collections import OrderedDict
from itertools import chain

from .dynamic import Dynamic
from .mountedtype import MountedType
from .structures import NonNull
from .utils import get_type


class Argument(MountedType):
    def __init__(
        self,
        type,
        default_value=None,
        description=None,
        name=None,
        required=False,
        _creation_counter=None,
    ):
        super(Argument, self).__init__(_creation_counter=_creation_counter)

        if required:
            type = NonNull(type)

        self.name = name
        self._type = type
        self.default_value = default_value
        self.description = description

    @property
    def type(self):
        return get_type(self._type)

    def __eq__(self, other):
        return isinstance(other, Argument) and (
            self.name == other.name
            and self.type == other.type
            and self.default_value == other.default_value
            and self.description == other.description
        )


def to_arguments(args, extra_args=None):
    from .unmountedtype import UnmountedType
    from .field import Field
    from .inputfield import InputField

    if extra_args:
        extra_args = sorted(extra_args.items(), key=lambda f: f[1])
    else:
        extra_args = []
    iter_arguments = chain(args.items(), extra_args)
    arguments = OrderedDict()
    for default_name, arg in iter_arguments:
        if isinstance(arg, Dynamic):
            arg = arg.get_type()
            if arg is None:
                # If the Dynamic type returned None
                # then we skip the Argument
                continue

        if isinstance(arg, UnmountedType):
            arg = Argument.mounted(arg)

        if isinstance(arg, (InputField, Field)):
            raise ValueError(
                "Expected {} to be Argument, but received {}. Try using Argument({}).".format(
                    default_name, type(arg).__name__, arg.type
                )
            )

        if not isinstance(arg, Argument):
            raise ValueError('Unknown argument "{}".'.format(default_name))

        arg_name = default_name or arg.name
        assert (
            arg_name not in arguments
        ), 'More than one Argument have same name "{}".'.format(
            arg_name
        )
        arguments[arg_name] = arg

    return arguments

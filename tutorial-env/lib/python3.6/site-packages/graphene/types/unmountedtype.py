from ..utils.orderedtype import OrderedType


class UnmountedType(OrderedType):
    """
    This class acts a proxy for a Graphene Type, so it can be mounted
    dynamically as Field, InputField or Argument.

    Instead of writing
    >>> class MyObjectType(ObjectType):
    >>>     my_field = Field(String, description='Description here')

    It let you write
    >>> class MyObjectType(ObjectType):
    >>>     my_field = String(description='Description here')
    """

    def __init__(self, *args, **kwargs):
        super(UnmountedType, self).__init__()
        self.args = args
        self.kwargs = kwargs

    def get_type(self):
        """
        This function is called when the UnmountedType instance
        is mounted (as a Field, InputField or Argument)
        """
        raise NotImplementedError("get_type not implemented in {}".format(self))

    def mount_as(self, _as):
        return _as.mounted(self)

    def Field(self):  # noqa: N802
        """
        Mount the UnmountedType as Field
        """
        from .field import Field

        return self.mount_as(Field)

    def InputField(self):  # noqa: N802
        """
        Mount the UnmountedType as InputField
        """
        from .inputfield import InputField

        return self.mount_as(InputField)

    def Argument(self):  # noqa: N802
        """
        Mount the UnmountedType as Argument
        """
        from .argument import Argument

        return self.mount_as(Argument)

    def __eq__(self, other):
        return self is other or (
            isinstance(other, UnmountedType)
            and self.get_type() == other.get_type()
            and self.args == other.args
            and self.kwargs == other.kwargs
        )

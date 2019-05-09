from .unmountedtype import UnmountedType
from .utils import get_type


class Structure(UnmountedType):
    """
    A structure is a GraphQL type instance that
    wraps a main type with certain structure.
    """

    def __init__(self, of_type, *args, **kwargs):
        super(Structure, self).__init__(*args, **kwargs)
        if not isinstance(of_type, Structure) and isinstance(of_type, UnmountedType):
            cls_name = type(self).__name__
            of_type_name = type(of_type).__name__
            raise Exception(
                "{} could not have a mounted {}() as inner type. Try with {}({}).".format(
                    cls_name, of_type_name, cls_name, of_type_name
                )
            )
        self._of_type = of_type

    @property
    def of_type(self):
        return get_type(self._of_type)

    def get_type(self):
        """
        This function is called when the unmounted type (List or NonNull instance)
        is mounted (as a Field, InputField or Argument)
        """
        return self


class List(Structure):
    """
    List Modifier

    A list is a kind of type marker, a wrapping type which points to another
    type. Lists are often created within the context of defining the fields of
    an object type.
    """

    def __str__(self):
        return "[{}]".format(self.of_type)

    def __eq__(self, other):
        return isinstance(other, List) and (
            self.of_type == other.of_type
            and self.args == other.args
            and self.kwargs == other.kwargs
        )


class NonNull(Structure):
    """
    Non-Null Modifier

    A non-null is a kind of type marker, a wrapping type which points to another
    type. Non-null types enforce that their values are never null and can ensure
    an error is raised if this ever occurs during a request. It is useful for
    fields which you can make a strong guarantee on non-nullability, for example
    usually the id field of a database row will never be null.

    Note: the enforcement of non-nullability occurs within the executor.
    """

    def __init__(self, *args, **kwargs):
        super(NonNull, self).__init__(*args, **kwargs)
        assert not isinstance(self._of_type, NonNull), (
            "Can only create NonNull of a Nullable GraphQLType but got: {}."
        ).format(self._of_type)

    def __str__(self):
        return "{}!".format(self.of_type)

    def __eq__(self, other):
        return isinstance(other, NonNull) and (
            self.of_type == other.of_type
            and self.args == other.args
            and self.kwargs == other.kwargs
        )

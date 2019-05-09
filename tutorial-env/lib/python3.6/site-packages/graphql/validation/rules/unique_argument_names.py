from ...error import GraphQLError
from .base import ValidationRule

# Necessary for static type checking
if False:  # flake8: noqa
    from ..validation import ValidationContext
    from ...language.ast import Field, InlineFragment, Argument, Name
    from typing import Any, List, Union, Dict


class UniqueArgumentNames(ValidationRule):
    __slots__ = ("known_arg_names",)

    def __init__(self, context):
        # type: (ValidationContext) -> None
        super(UniqueArgumentNames, self).__init__(context)
        self.known_arg_names = {}  # type: Dict[str, Name]

    def enter_Field(
        self,
        node,  # type: Field
        key,  # type: int
        parent,  # type: Union[List[Union[Field, InlineFragment]], List[Field]]
        path,  # type: List[Union[int, str]]
        ancestors,  # type: List[Any]
    ):
        # type: (...) -> None
        self.known_arg_names = {}

    def enter_Directive(self, node, key, parent, path, ancestors):
        self.known_arg_names = {}

    def enter_Argument(
        self,
        node,  # type: Argument
        key,  # type: int
        parent,  # type: List[Argument]
        path,  # type: List[Union[int, str]]
        ancestors,  # type: List[Any]
    ):
        # type: (...) -> bool
        arg_name = node.name.value

        if arg_name in self.known_arg_names:
            self.context.report_error(
                GraphQLError(
                    self.duplicate_arg_message(arg_name),
                    [self.known_arg_names[arg_name], node.name],
                )
            )
        else:
            self.known_arg_names[arg_name] = node.name
        return False

    @staticmethod
    def duplicate_arg_message(field):
        return 'There can only be one argument named "{}".'.format(field)

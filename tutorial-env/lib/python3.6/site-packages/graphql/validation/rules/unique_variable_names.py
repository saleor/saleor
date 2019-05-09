from ...error import GraphQLError
from .base import ValidationRule

# Necessary for static type checking
if False:  # flake8: noqa
    from ..validation import ValidationContext
    from ...language.ast import Document, OperationDefinition
    from typing import List, Union, Dict


class UniqueVariableNames(ValidationRule):
    __slots__ = ("known_variable_names",)

    def __init__(self, context):
        # type: (ValidationContext) -> None
        super(UniqueVariableNames, self).__init__(context)
        self.known_variable_names = {}  # type: Dict[str, str]

    def enter_OperationDefinition(
        self,
        node,  # type: OperationDefinition
        key,  # type: int
        parent,  # type: List[OperationDefinition]
        path,  # type: List[Union[int, str]]
        ancestors,  # type: List[Document]
    ):
        # type: (...) -> None
        self.known_variable_names = {}

    def enter_VariableDefinition(self, node, key, parent, path, ancestors):
        variable_name = node.variable.name.value
        if variable_name in self.known_variable_names:
            self.context.report_error(
                GraphQLError(
                    self.duplicate_variable_message(variable_name),
                    [self.known_variable_names[variable_name], node.variable.name],
                )
            )
        else:
            self.known_variable_names[variable_name] = node.variable.name

    @staticmethod
    def duplicate_variable_message(operation_name):
        return 'There can be only one variable named "{}".'.format(operation_name)

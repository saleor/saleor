from ...error import GraphQLError
from .base import ValidationRule

# Necessary for static type checking
if False:  # flake8: noqa
    from ..validation import ValidationContext
    from ...language.ast import Document, OperationDefinition
    from typing import List, Union, Set


class NoUndefinedVariables(ValidationRule):
    __slots__ = ("defined_variable_names",)

    def __init__(self, context):
        # type: (ValidationContext) -> None
        self.defined_variable_names = set()  # type: Set[str]
        super(NoUndefinedVariables, self).__init__(context)

    @staticmethod
    def undefined_var_message(var_name, op_name=None):
        if op_name:
            return 'Variable "${}" is not defined by operation "{}".'.format(
                var_name, op_name
            )
        return 'Variable "${}" is not defined.'.format(var_name)

    def enter_OperationDefinition(
        self,
        operation,  # type: OperationDefinition
        key,  # type: int
        parent,  # type: List[OperationDefinition]
        path,  # type: List[Union[int, str]]
        ancestors,  # type: List[Document]
    ):
        # type: (...) -> None
        self.defined_variable_names = set()

    def leave_OperationDefinition(
        self,
        operation,  # type: OperationDefinition
        key,  # type: int
        parent,  # type: List[OperationDefinition]
        path,  # type: List[str]
        ancestors,  # type: List[Document]
    ):
        # type: (...) -> None
        usages = self.context.get_recursive_variable_usages(operation)

        for variable_usage in usages:
            node = variable_usage.node
            var_name = node.name.value
            if var_name not in self.defined_variable_names:
                self.context.report_error(
                    GraphQLError(
                        self.undefined_var_message(
                            var_name, operation.name and operation.name.value
                        ),
                        [node, operation],
                    )
                )

    def enter_VariableDefinition(self, node, key, parent, path, ancestors):
        self.defined_variable_names.add(node.variable.name.value)

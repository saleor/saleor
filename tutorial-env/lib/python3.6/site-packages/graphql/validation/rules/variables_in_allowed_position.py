from ...error import GraphQLError
from ...type.definition import GraphQLNonNull
from ...utils.type_comparators import is_type_sub_type_of
from ...utils.type_from_ast import type_from_ast
from .base import ValidationRule

# Necessary for static type checking
if False:  # flake8: noqa
    from ..validation import ValidationContext
    from ...language.ast import Document, OperationDefinition, VariableDefinition
    from typing import List, Union, Dict, Any


class VariablesInAllowedPosition(ValidationRule):
    __slots__ = "var_def_map"

    def __init__(self, context):
        # type: (ValidationContext) -> None
        super(VariablesInAllowedPosition, self).__init__(context)
        self.var_def_map = {}  # type: Dict[str, VariableDefinition]

    def enter_OperationDefinition(
        self,
        node,  # type: OperationDefinition
        key,  # type: int
        parent,  # type: List[OperationDefinition]
        path,  # type: List[Union[int, str]]
        ancestors,  # type: List[Document]
    ):
        # type: (...) -> None
        self.var_def_map = {}

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

        for usage in usages:
            node = usage.node
            type = usage.type
            var_name = node.name.value
            var_def = self.var_def_map.get(var_name)
            if var_def and type:
                # A var type is allowed if it is the same or more strict (e.g. is
                # a subtype of) than the expected type. It can be more strict if
                # the variable type is non-null when the expected type is nullable.
                # If both are list types, the variable item type can be more strict
                # than the expected item type (contravariant).
                schema = self.context.get_schema()
                var_type = type_from_ast(schema, var_def.type)
                if var_type and not is_type_sub_type_of(
                    schema, self.effective_type(var_type, var_def), type
                ):
                    self.context.report_error(
                        GraphQLError(
                            self.bad_var_pos_message(var_name, var_type, type),
                            [var_def, node],
                        )
                    )

    def enter_VariableDefinition(
        self,
        node,  # type: VariableDefinition
        key,  # type: int
        parent,  # type: Any
        path,  # type: List[str]
        ancestors,  # type: List[Document]
    ):

        self.var_def_map[node.variable.name.value] = node

    @staticmethod
    def effective_type(var_type, var_def):
        if not var_def.default_value or isinstance(var_type, GraphQLNonNull):
            return var_type

        return GraphQLNonNull(var_type)

    @staticmethod
    def bad_var_pos_message(var_name, var_type, expected_type):
        return 'Variable "{}" of type "{}" used in position expecting type "{}".'.format(
            var_name, var_type, expected_type
        )

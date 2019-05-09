from ...error import GraphQLError
from ...language.printer import print_ast
from ...type.definition import is_input_type
from ...utils.type_from_ast import type_from_ast
from .base import ValidationRule


class VariablesAreInputTypes(ValidationRule):
    def enter_VariableDefinition(self, node, key, parent, path, ancestors):
        type = type_from_ast(self.context.get_schema(), node.type)

        if type and not is_input_type(type):
            self.context.report_error(
                GraphQLError(
                    self.non_input_type_on_variable_message(
                        node.variable.name.value, print_ast(node.type)
                    ),
                    [node.type],
                )
            )

    @staticmethod
    def non_input_type_on_variable_message(variable_name, type_name):
        return 'Variable "${}" cannot be non-input type "{}".'.format(
            variable_name, type_name
        )

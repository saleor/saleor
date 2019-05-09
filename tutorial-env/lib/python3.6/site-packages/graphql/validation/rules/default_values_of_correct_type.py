from ...error import GraphQLError
from ...language.printer import print_ast
from ...type.definition import GraphQLNonNull
from ...utils.is_valid_literal_value import is_valid_literal_value
from .base import ValidationRule

# Necessary for static type checking
if False:  # flake8: noqa
    from ...language.ast import Document, OperationDefinition, SelectionSet
    from typing import List, Union


class DefaultValuesOfCorrectType(ValidationRule):
    def enter_VariableDefinition(self, node, key, parent, path, ancestors):
        name = node.variable.name.value
        default_value = node.default_value
        type = self.context.get_input_type()

        if isinstance(type, GraphQLNonNull) and default_value:
            self.context.report_error(
                GraphQLError(
                    self.default_for_non_null_arg_message(name, type, type.of_type),
                    [default_value],
                )
            )

        if type and default_value:
            errors = is_valid_literal_value(type, default_value)
            if errors:
                self.context.report_error(
                    GraphQLError(
                        self.bad_value_for_default_arg_message(
                            name, type, print_ast(default_value), errors
                        ),
                        [default_value],
                    )
                )
        return False

    def enter_SelectionSet(
        self,
        node,  # type: SelectionSet
        key,  # type: str
        parent,  # type: OperationDefinition
        path,  # type: List[Union[int, str]]
        ancestors,  # type: List[Union[List[OperationDefinition], Document]]
    ):
        # type: (...) -> bool
        return False

    def enter_FragmentDefinition(self, node, key, parent, path, ancestors):
        return False

    @staticmethod
    def default_for_non_null_arg_message(var_name, type, guess_type):
        return (
            u'Variable "${}" of type "{}" is required and will not use the default value. '
            u'Perhaps you meant to use type "{}".'.format(var_name, type, guess_type)
        )

    @staticmethod
    def bad_value_for_default_arg_message(var_name, type, value, verbose_errors):
        message = (u"\n" + u"\n".join(verbose_errors)) if verbose_errors else u""
        return u'Variable "${}" of type "{}" has invalid default value: {}.{}'.format(
            var_name, type, value, message
        )

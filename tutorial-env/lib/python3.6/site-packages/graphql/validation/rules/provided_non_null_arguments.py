from ...error import GraphQLError
from ...type.definition import GraphQLNonNull
from .base import ValidationRule

# Necessary for static type checking
if False:  # flake8: noqa
    from ...language.ast import Field, InlineFragment
    from typing import Any, List, Optional, Union


class ProvidedNonNullArguments(ValidationRule):
    def leave_Field(
        self,
        node,  # type: Field
        key,  # type: int
        parent,  # type: Union[List[Union[Field, InlineFragment]], List[Field]]
        path,  # type: List[Union[int, str]]
        ancestors,  # type: List[Any]
    ):
        # type: (...) -> Optional[Any]
        field_def = self.context.get_field_def()
        if not field_def:
            return False

        arg_asts = node.arguments or []
        arg_ast_map = {arg.name.value: arg for arg in arg_asts}

        for arg_name, arg_def in field_def.args.items():
            arg_ast = arg_ast_map.get(arg_name, None)
            if not arg_ast and isinstance(arg_def.type, GraphQLNonNull):
                self.context.report_error(
                    GraphQLError(
                        self.missing_field_arg_message(
                            node.name.value, arg_name, arg_def.type
                        ),
                        [node],
                    )
                )
        return None

    def leave_Directive(self, node, key, parent, path, ancestors):
        directive_def = self.context.get_directive()
        if not directive_def:
            return False

        arg_asts = node.arguments or []
        arg_ast_map = {arg.name.value: arg for arg in arg_asts}

        for arg_name, arg_def in directive_def.args.items():
            arg_ast = arg_ast_map.get(arg_name, None)
            if not arg_ast and isinstance(arg_def.type, GraphQLNonNull):
                self.context.report_error(
                    GraphQLError(
                        self.missing_directive_arg_message(
                            node.name.value, arg_name, arg_def.type
                        ),
                        [node],
                    )
                )

    @staticmethod
    def missing_field_arg_message(name, arg_name, type):
        return 'Field "{}" argument "{}" of type "{}" is required but not provided.'.format(
            name, arg_name, type
        )

    @staticmethod
    def missing_directive_arg_message(name, arg_name, type):
        return 'Directive "{}" argument "{}" of type "{}" is required but not provided.'.format(
            name, arg_name, type
        )

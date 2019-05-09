from ..language import ast

# Necessary for static type checking
if False:  # flake8: noqa
    from ..language.ast import Document, OperationDefinition
    from typing import Optional


def get_operation_ast(document_ast, operation_name=None):
    # type: (Document, Optional[str]) -> Optional[OperationDefinition]
    operation = None

    for definition in document_ast.definitions:
        if isinstance(definition, ast.OperationDefinition):
            if not operation_name:
                # If no operation name is provided, only return an Operation if it is the only one present in the
                # document. This means that if we've encountered a second operation as we were iterating over the
                # definitions in the document, there are more than one Operation defined, and we should return None.
                if operation:
                    return None

                operation = definition

            elif definition.name and definition.name.value == operation_name:
                return definition

    return operation

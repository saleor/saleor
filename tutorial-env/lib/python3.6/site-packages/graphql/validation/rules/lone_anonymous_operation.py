from ...error import GraphQLError
from ...language import ast
from .base import ValidationRule

# Necessary for static type checking
if False:  # flake8: noqa
    from ..validation import ValidationContext
    from ...language.ast import Document, OperationDefinition
    from typing import Any, List, Optional, Union


class LoneAnonymousOperation(ValidationRule):
    __slots__ = ("operation_count",)

    def __init__(self, context):
        # type: (ValidationContext) -> None
        self.operation_count = 0
        super(LoneAnonymousOperation, self).__init__(context)

    def enter_Document(self, node, key, parent, path, ancestors):
        # type: (Document, Optional[Any], Optional[Any], List, List) -> None
        self.operation_count = sum(
            1
            for definition in node.definitions
            if isinstance(definition, ast.OperationDefinition)
        )

    def enter_OperationDefinition(
        self,
        node,  # type: OperationDefinition
        key,  # type: int
        parent,  # type: List[OperationDefinition]
        path,  # type: List[Union[int, str]]
        ancestors,  # type: List[Document]
    ):
        # type: (...) -> None
        if not node.name and self.operation_count > 1:
            self.context.report_error(
                GraphQLError(self.anonymous_operation_not_alone_message(), [node])
            )

    @staticmethod
    def anonymous_operation_not_alone_message():
        return "This anonymous operation must be the only defined operation."

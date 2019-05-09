from ...error import GraphQLError
from .base import ValidationRule

# Necessary for static type checking
if False:  # flake8: noqa
    from ..validation import ValidationContext
    from ...language.ast import Document, OperationDefinition, Name
    from typing import Any, List, Optional, Union, Dict


class UniqueOperationNames(ValidationRule):
    __slots__ = ("known_operation_names",)

    def __init__(self, context):
        # type: (ValidationContext) -> None
        super(UniqueOperationNames, self).__init__(context)
        self.known_operation_names = {}  # type: Dict[str, Name]

    def enter_OperationDefinition(
        self,
        node,  # type: OperationDefinition
        key,  # type: int
        parent,  # type: List[OperationDefinition]
        path,  # type: List[Union[int, str]]
        ancestors,  # type: List[Document]
    ):
        # type: (...) -> Optional[Any]
        operation_name = node.name
        if not operation_name:
            return None

        if operation_name.value in self.known_operation_names:
            self.context.report_error(
                GraphQLError(
                    self.duplicate_operation_name_message(operation_name.value),
                    [self.known_operation_names[operation_name.value], operation_name],
                )
            )
        else:
            self.known_operation_names[operation_name.value] = operation_name
        return False

    def enter_FragmentDefinition(self, node, key, parent, path, ancestors):
        return False

    @staticmethod
    def duplicate_operation_name_message(operation_name):
        return 'There can only be one operation named "{}".'.format(operation_name)

from ...error import GraphQLError
from .base import ValidationRule

# Necessary for static type checking
if False:  # flake8: noqa
    from ..validation import ValidationContext
    from ...language.ast import Document, OperationDefinition, FragmentDefinition
    from typing import List, Union, Any, Optional


class NoUnusedFragments(ValidationRule):
    __slots__ = (
        "fragment_definitions",
        "operation_definitions",
        "fragment_adjacencies",
        "spread_names",
    )

    def __init__(self, context):
        # type: (ValidationContext) -> None
        super(NoUnusedFragments, self).__init__(context)
        self.operation_definitions = []  # type: List[OperationDefinition]
        self.fragment_definitions = []  # type: List[FragmentDefinition]

    def enter_OperationDefinition(
        self,
        node,  # type: OperationDefinition
        key,  # type: int
        parent,  # type: List[OperationDefinition]
        path,  # type: List[Union[int, str]]
        ancestors,  # type: List[Document]
    ):
        # type: (...) -> bool
        self.operation_definitions.append(node)
        return False

    def enter_FragmentDefinition(self, node, key, parent, path, ancestors):
        self.fragment_definitions.append(node)
        return False

    def leave_Document(self, node, key, parent, path, ancestors):
        # type: (Document, Optional[Any], Optional[Any], List, List) -> None
        fragment_names_used = set()

        for operation in self.operation_definitions:
            fragments = self.context.get_recursively_referenced_fragments(operation)
            for fragment in fragments:
                fragment_names_used.add(fragment.name.value)

        for fragment_definition in self.fragment_definitions:
            if fragment_definition.name.value not in fragment_names_used:
                self.context.report_error(
                    GraphQLError(
                        self.unused_fragment_message(fragment_definition.name.value),
                        [fragment_definition],
                    )
                )

    @staticmethod
    def unused_fragment_message(fragment_name):
        return 'Fragment "{}" is never used.'.format(fragment_name)

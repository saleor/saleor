from ...error import GraphQLError
from .base import ValidationRule

# Necessary for static type checking
if False:  # flake8: noqa
    from ..validation import ValidationContext
    from ...language.ast import Document, OperationDefinition, Name
    from typing import List, Union, Dict


class UniqueFragmentNames(ValidationRule):
    __slots__ = ("known_fragment_names",)

    def __init__(self, context):
        # type: (ValidationContext) -> None
        super(UniqueFragmentNames, self).__init__(context)
        self.known_fragment_names = {}  # type: Dict[str, Name]

    def enter_OperationDefinition(
        self,
        node,  # type: OperationDefinition
        key,  # type: int
        parent,  # type: List[OperationDefinition]
        path,  # type: List[Union[int, str]]
        ancestors,  # type: List[Document]
    ):
        # type: (...) -> bool
        return False

    def enter_FragmentDefinition(self, node, key, parent, path, ancestors):
        fragment_name = node.name.value
        if fragment_name in self.known_fragment_names:
            self.context.report_error(
                GraphQLError(
                    self.duplicate_fragment_name_message(fragment_name),
                    [self.known_fragment_names[fragment_name], node.name],
                )
            )
        else:
            self.known_fragment_names[fragment_name] = node.name
        return False

    @staticmethod
    def duplicate_fragment_name_message(field):
        return 'There can only be one fragment named "{}".'.format(field)

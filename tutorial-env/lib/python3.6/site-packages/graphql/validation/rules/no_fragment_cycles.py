from ...error import GraphQLError
from .base import ValidationRule

# Necessary for static type checking
if False:  # flake8: noqa
    from ..validation import ValidationContext
    from ...language.ast import Document, OperationDefinition, FragmentSpread
    from ...error import GraphQLError
    from typing import List, Union, Dict, Set


class NoFragmentCycles(ValidationRule):
    __slots__ = "errors", "visited_frags", "spread_path", "spread_path_index_by_name"

    def __init__(self, context):
        # type: (ValidationContext) -> None
        super(NoFragmentCycles, self).__init__(context)
        self.errors = []  # type: List[GraphQLError]
        self.visited_frags = set()  # type: Set[str]
        self.spread_path = []  # type: List[FragmentSpread]
        self.spread_path_index_by_name = {}  # type: Dict[str, int]

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
        if node.name.value not in self.visited_frags:
            self.detect_cycle_recursive(node)
        return False

    def detect_cycle_recursive(self, fragment):
        fragment_name = fragment.name.value
        self.visited_frags.add(fragment_name)

        spread_nodes = self.context.get_fragment_spreads(fragment.selection_set)
        if not spread_nodes:
            return

        self.spread_path_index_by_name[fragment_name] = len(self.spread_path)

        for spread_node in spread_nodes:
            spread_name = spread_node.name.value
            cycle_index = self.spread_path_index_by_name.get(spread_name)

            if cycle_index is None:
                self.spread_path.append(spread_node)
                if spread_name not in self.visited_frags:
                    spread_fragment = self.context.get_fragment(spread_name)
                    if spread_fragment:
                        self.detect_cycle_recursive(spread_fragment)
                self.spread_path.pop()
            else:
                cycle_path = self.spread_path[cycle_index:]
                self.context.report_error(
                    GraphQLError(
                        self.cycle_error_message(
                            spread_name, [s.name.value for s in cycle_path]
                        ),
                        cycle_path + [spread_node],
                    )
                )

        self.spread_path_index_by_name[fragment_name] = None

    @staticmethod
    def cycle_error_message(fragment_name, spread_names):
        via = " via {}".format(", ".join(spread_names)) if spread_names else ""
        return 'Cannot spread fragment "{}" within itself{}.'.format(fragment_name, via)

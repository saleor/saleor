from ...error import GraphQLError
from ...utils.type_comparators import do_types_overlap
from ...utils.type_from_ast import type_from_ast
from .base import ValidationRule

# Necessary for static type checking
if False:  # flake8: noqa
    from ...language.ast import Field, InlineFragment
    from typing import Any, List, Union


class PossibleFragmentSpreads(ValidationRule):
    def enter_InlineFragment(
        self,
        node,  # type: InlineFragment
        key,  # type: int
        parent,  # type: List[Union[Field, InlineFragment]]
        path,  # type: List[Union[int, str]]
        ancestors,  # type: List[Any]
    ):
        # type: (...) -> None
        frag_type = self.context.get_type()
        parent_type = self.context.get_parent_type()
        schema = self.context.get_schema()
        if (
            frag_type
            and parent_type
            and not do_types_overlap(schema, frag_type, parent_type)  # type: ignore
        ):
            self.context.report_error(
                GraphQLError(
                    self.type_incompatible_anon_spread_message(parent_type, frag_type),
                    [node],
                )
            )

    def enter_FragmentSpread(self, node, key, parent, path, ancestors):
        frag_name = node.name.value
        frag_type = self.get_fragment_type(self.context, frag_name)
        parent_type = self.context.get_parent_type()
        schema = self.context.get_schema()
        if (
            frag_type
            and parent_type
            and not do_types_overlap(schema, frag_type, parent_type)
        ):
            self.context.report_error(
                GraphQLError(
                    self.type_incompatible_spread_message(
                        frag_name, parent_type, frag_type
                    ),
                    [node],
                )
            )

    @staticmethod
    def get_fragment_type(context, name):
        frag = context.get_fragment(name)
        return frag and type_from_ast(context.get_schema(), frag.type_condition)

    @staticmethod
    def type_incompatible_spread_message(frag_name, parent_type, frag_type):
        return "Fragment {} cannot be spread here as objects of type {} can never be of type {}".format(
            frag_name, parent_type, frag_type
        )

    @staticmethod
    def type_incompatible_anon_spread_message(parent_type, frag_type):
        return "Fragment cannot be spread here as objects of type {} can never be of type {}".format(
            parent_type, frag_type
        )

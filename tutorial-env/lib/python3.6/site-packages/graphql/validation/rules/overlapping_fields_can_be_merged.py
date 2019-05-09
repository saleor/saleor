import itertools
from collections import OrderedDict

from ...error import GraphQLError
from ...language import ast
from ...language.printer import print_ast
from ...pyutils.pair_set import PairSet
from ...type.definition import (
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    get_named_type,
    is_leaf_type,
)
from ...utils.type_comparators import is_equal_type
from ...utils.type_from_ast import type_from_ast
from .base import ValidationRule

# Necessary for static type checking
if False:  # flake8: noqa
    from ..validation import ValidationContext
    from ...language.ast import (
        Node,
        OperationDefinition,
        Field,
        Argument,
        InlineFragment,
        SelectionSet,
    )
    from ...type.definition import GraphQLUnionType, GraphQLField, GraphQLScalarType
    from ...pyutils.pair_set import PairSet
    from typing import List, Union, Any, Optional, Dict, Tuple


class OverlappingFieldsCanBeMerged(ValidationRule):
    __slots__ = ("_compared_fragments", "_cached_fields_and_fragment_names")

    def __init__(self, context):
        # type: (ValidationContext) -> None
        super(OverlappingFieldsCanBeMerged, self).__init__(context)
        # A memoization for when two fragments are compared "between" each other for
        # conflicts. Two fragments may be compared many times, so memoizing this can
        # dramatically improve the performance of this validator.
        self._compared_fragments = PairSet()

        # A cache for the "field map" and list of fragment names found in any given
        # selection set. Selection sets may be asked for this information multiple
        # times, so this improves the performance of this validator.
        self._cached_fields_and_fragment_names = {}  # type: Dict[SelectionSet, Tuple[Dict[str, List[Tuple[Union[GraphQLInterfaceType, GraphQLObjectType, None], Field, GraphQLField]]], List[str]]]

    def leave_SelectionSet(
        self,
        node,  # type: SelectionSet
        key,  # type: str
        parent,  # type: Union[Field, InlineFragment, OperationDefinition]
        path,  # type: List[Union[int, str]]
        ancestors,  # type: List[Any]
    ):
        # type: (...) -> None
        # Note: we validate on the reverse traversal so deeper conflicts will be
        # caught first, for correct calculation of mutual exclusivity and for
        # clearer error messages.
        # field_map = _collect_field_asts_and_defs(
        #     self.context,
        #     self.context.get_parent_type(),
        #     node
        # )

        # conflicts = _find_conflicts(self.context, False, field_map, self.compared_set)
        conflicts = _find_conflicts_within_selection_set(
            self.context,
            self._cached_fields_and_fragment_names,
            self._compared_fragments,
            self.context.get_parent_type(),
            node,
        )

        for (reason_name, reason), fields1, fields2 in conflicts:
            self.context.report_error(
                GraphQLError(
                    self.fields_conflict_message(reason_name, reason),
                    list(fields1) + list(fields2),
                )
            )

    @staticmethod
    def same_type(type1, type2):
        return is_equal_type(type1, type2)
        # return type1.is_same_type(type2)

    @classmethod
    def fields_conflict_message(cls, reason_name, reason):
        return (
            'Fields "{}" conflict because {}. '
            "Use different aliases on the fields to fetch both if this was "
            "intentional."
        ).format(reason_name, cls.reason_message(reason))

    @classmethod
    def reason_message(cls, reason):
        if isinstance(reason, list):
            return " and ".join(
                'subfields "{}" conflict because {}'.format(
                    reason_name, cls.reason_message(sub_reason)
                )
                for reason_name, sub_reason in reason
            )

        return reason


# Algorithm:
#
#  Conflicts occur when two fields exist in a query which will produce the same
#  response name, but represent differing values, thus creating a conflict.
#  The algorithm below finds all conflicts via making a series of comparisons
#  between fields. In order to compare as few fields as possible, this makes
#  a series of comparisons "within" sets of fields and "between" sets of fields.
#
#  Given any selection set, a collection produces both a set of fields by
#  also including all inline fragments, as well as a list of fragments
#  referenced by fragment spreads.
#
#  A) Each selection set represented in the document first compares "within" its
#  collected set of fields, finding any conflicts between every pair of
#  overlapping fields.
#  Note: This is the only time that a the fields "within" a set are compared
#  to each other. After this only fields "between" sets are compared.
#
#  B) Also, if any fragment is referenced in a selection set, then a
#  comparison is made "between" the original set of fields and the
#  referenced fragment.
#
#  C) Also, if multiple fragments are referenced, then comparisons
#  are made "between" each referenced fragment.
#
#  D) When comparing "between" a set of fields and a referenced fragment, first
#  a comparison is made between each field in the original set of fields and
#  each field in the the referenced set of fields.
#
#  E) Also, if any fragment is referenced in the referenced selection set,
#  then a comparison is made "between" the original set of fields and the
#  referenced fragment (recursively referring to step D).
#
#  F) When comparing "between" two fragments, first a comparison is made between
#  each field in the first referenced set of fields and each field in the the
#  second referenced set of fields.
#
#  G) Also, any fragments referenced by the first must be compared to the
#  second, and any fragments referenced by the second must be compared to the
#  first (recursively referring to step F).
#
#  H) When comparing two fields, if both have selection sets, then a comparison
#  is made "between" both selection sets, first comparing the set of fields in
#  the first selection set with the set of fields in the second.
#
#  I) Also, if any fragment is referenced in either selection set, then a
#  comparison is made "between" the other set of fields and the
#  referenced fragment.
#
#  J) Also, if two fragments are referenced in both selection sets, then a
#  comparison is made "between" the two fragments.


def _find_conflicts_within_selection_set(
    context,  # type: ValidationContext
    cached_fields_and_fragment_names,  # type: Dict[SelectionSet, Tuple[Dict[str, List[Tuple[Union[GraphQLInterfaceType, GraphQLObjectType, None], Field, GraphQLField]]], List[str]]]
    compared_fragments,  # type: PairSet
    parent_type,  # type: Union[GraphQLInterfaceType, GraphQLObjectType, None]
    selection_set,  # type: SelectionSet
):
    # type: (...) ->  List[Tuple[Tuple[str, str], List[Node], List[Node]]]
    """Find all conflicts found "within" a selection set, including those found via spreading in fragments.

       Called when visiting each SelectionSet in the GraphQL Document.
    """
    conflicts = []  # type: List[Tuple[Tuple[str, str], List[Node], List[Node]]]
    field_map, fragment_names = _get_fields_and_fragments_names(
        context, cached_fields_and_fragment_names, parent_type, selection_set
    )

    # (A) Find all conflicts "within" the fields of this selection set.
    # Note: this is the *only place* `collect_conflicts_within` is called.
    _collect_conflicts_within(
        context,
        conflicts,
        cached_fields_and_fragment_names,
        compared_fragments,
        field_map,
    )

    # (B) Then collect conflicts between these fields and those represented by
    # each spread fragment name found.
    for i, fragment_name in enumerate(fragment_names):
        _collect_conflicts_between_fields_and_fragment(
            context,
            conflicts,
            cached_fields_and_fragment_names,
            compared_fragments,
            False,
            field_map,
            fragment_name,
        )

        # (C) Then compare this fragment with all other fragments found in this
        # selection set to collect conflicts within fragments spread together.
        # This compares each item in the list of fragment names to every other item
        # in that same list (except for itself).
        for other_fragment_name in fragment_names[i + 1 :]:
            _collect_conflicts_between_fragments(
                context,
                conflicts,
                cached_fields_and_fragment_names,
                compared_fragments,
                False,
                fragment_name,
                other_fragment_name,
            )

    return conflicts


def _collect_conflicts_between_fields_and_fragment(
    context,  # type: ValidationContext
    conflicts,  # type: List[Tuple[Tuple[str, str], List[Node], List[Node]]]
    cached_fields_and_fragment_names,  # type: Dict[SelectionSet, Tuple[Dict[str, List[Tuple[Union[GraphQLInterfaceType, GraphQLObjectType, None], Field, GraphQLField]]], List[str]]]
    compared_fragments,  # type: PairSet
    are_mutually_exclusive,  # type: bool
    field_map,  # type: Dict[str, List[Tuple[Union[GraphQLInterfaceType, GraphQLObjectType, None], Field, GraphQLField]]]
    fragment_name,  # type: str
):

    fragment = context.get_fragment(fragment_name)

    if not fragment:
        return None

    field_map2, fragment_names2 = _get_referenced_fields_and_fragment_names(
        context, cached_fields_and_fragment_names, fragment
    )

    # (D) First collect any conflicts between the provided collection of fields
    # and the collection of fields represented by the given fragment.
    _collect_conflicts_between(
        context,
        conflicts,
        cached_fields_and_fragment_names,
        compared_fragments,
        are_mutually_exclusive,
        field_map,
        field_map2,
    )

    # (E) Then collect any conflicts between the provided collection of fields
    # and any fragment names found in the given fragment.
    for fragment_name2 in fragment_names2:
        _collect_conflicts_between_fields_and_fragment(
            context,
            conflicts,
            cached_fields_and_fragment_names,
            compared_fragments,
            are_mutually_exclusive,
            field_map,
            fragment_name2,
        )


# Collect all conflicts found between two fragments, including via spreading in
# any nested fragments
def _collect_conflicts_between_fragments(
    context,  # type: ValidationContext
    conflicts,  # type: List[Tuple[Tuple[str, str], List[Node], List[Node]]]
    cached_fields_and_fragment_names,  # type: Dict[SelectionSet, Tuple[Dict[str, List[Tuple[Union[GraphQLInterfaceType, GraphQLObjectType, None], Field, GraphQLField]]], List[str]]]
    compared_fragments,  # type: PairSet
    are_mutually_exclusive,  # type: bool
    fragment_name1,  # type: str
    fragment_name2,  # type: str
):

    fragment1 = context.get_fragment(fragment_name1)
    fragment2 = context.get_fragment(fragment_name2)

    if not fragment1 or not fragment2:
        return None

    # No need to compare a fragment to itself.
    if fragment1 == fragment2:
        return None

    # Memoize so two fragments are not compared for conflicts more than once.
    if compared_fragments.has(fragment_name1, fragment_name2, are_mutually_exclusive):
        return None

    compared_fragments.add(fragment_name1, fragment_name2, are_mutually_exclusive)

    field_map1, fragment_names1 = _get_referenced_fields_and_fragment_names(
        context, cached_fields_and_fragment_names, fragment1
    )

    field_map2, fragment_names2 = _get_referenced_fields_and_fragment_names(
        context, cached_fields_and_fragment_names, fragment2
    )

    # (F) First, collect all conflicts between these two collections of fields
    # (not including any nested fragments)
    _collect_conflicts_between(
        context,
        conflicts,
        cached_fields_and_fragment_names,
        compared_fragments,
        are_mutually_exclusive,
        field_map1,
        field_map2,
    )

    # (G) Then collect conflicts between the first fragment and any nested
    # fragments spread in the second fragment.
    for _fragment_name2 in fragment_names2:
        _collect_conflicts_between_fragments(
            context,
            conflicts,
            cached_fields_and_fragment_names,
            compared_fragments,
            are_mutually_exclusive,
            fragment_name1,
            _fragment_name2,
        )

    # (G) Then collect conflicts between the second fragment and any nested
    # fragments spread in the first fragment.
    for _fragment_name1 in fragment_names1:
        _collect_conflicts_between_fragments(
            context,
            conflicts,
            cached_fields_and_fragment_names,
            compared_fragments,
            are_mutually_exclusive,
            _fragment_name1,
            fragment_name2,
        )

    conflicts,  # type: List[Tuple[Tuple[str, str], List[Node], List[Node]]]
    are_mutually_exclusive,  # type: bool


def _find_conflicts_between_sub_selection_sets(
    context,  # type: ValidationContext
    cached_fields_and_fragment_names,  # type: Dict[SelectionSet, Tuple[Dict[str, List[Tuple[Union[GraphQLInterfaceType, GraphQLObjectType, None], Field, GraphQLField]]], List[str]]]
    compared_fragments,  # type: PairSet
    are_mutually_exclusive,  # type: bool
    parent_type1,  # type: Union[GraphQLInterfaceType, GraphQLObjectType, None]
    selection_set1,  # type: SelectionSet
    parent_type2,  # type: Union[GraphQLInterfaceType, GraphQLObjectType, None]
    selection_set2,  # type: SelectionSet
):
    # type: (...) ->  List[Tuple[Tuple[str, str], List[Node], List[Node]]]
    """Find all conflicts found between two selection sets.

       Includes those found via spreading in fragments. Called when determining if conflicts exist
       between the sub-fields of two overlapping fields.
    """
    conflicts = []  # type: List[Tuple[Tuple[str, str], List[Node], List[Node]]]

    field_map1, fragment_names1 = _get_fields_and_fragments_names(
        context, cached_fields_and_fragment_names, parent_type1, selection_set1
    )

    field_map2, fragment_names2 = _get_fields_and_fragments_names(
        context, cached_fields_and_fragment_names, parent_type2, selection_set2
    )

    # (H) First, collect all conflicts between these two collections of field.
    _collect_conflicts_between(
        context,
        conflicts,
        cached_fields_and_fragment_names,
        compared_fragments,
        are_mutually_exclusive,
        field_map1,
        field_map2,
    )

    # (I) Then collect conflicts between the first collection of fields and
    # those referenced by each fragment name associated with the second.
    for fragment_name2 in fragment_names2:
        _collect_conflicts_between_fields_and_fragment(
            context,
            conflicts,
            cached_fields_and_fragment_names,
            compared_fragments,
            are_mutually_exclusive,
            field_map1,
            fragment_name2,
        )

    # (I) Then collect conflicts between the second collection of fields and
    #  those referenced by each fragment name associated with the first.
    for fragment_name1 in fragment_names1:
        _collect_conflicts_between_fields_and_fragment(
            context,
            conflicts,
            cached_fields_and_fragment_names,
            compared_fragments,
            are_mutually_exclusive,
            field_map2,
            fragment_name1,
        )

    # (J) Also collect conflicts between any fragment names by the first and
    # fragment names by the second. This compares each item in the first set of
    # names to each item in the second set of names.
    for fragment_name1 in fragment_names1:
        for fragment_name2 in fragment_names2:
            _collect_conflicts_between_fragments(
                context,
                conflicts,
                cached_fields_and_fragment_names,
                compared_fragments,
                are_mutually_exclusive,
                fragment_name1,
                fragment_name2,
            )

    return conflicts


def _collect_conflicts_within(
    context,  # type: ValidationContext
    conflicts,  # type: List[Tuple[Tuple[str, str], List[Node], List[Node]]]
    cached_fields_and_fragment_names,  # type: Dict[SelectionSet, Tuple[Dict[str, List[Tuple[Union[GraphQLInterfaceType, GraphQLObjectType, None], Field, GraphQLField]]], List[str]]]
    compared_fragments,  # type: PairSet
    field_map,  # type: Dict[str, List[Tuple[Union[GraphQLInterfaceType, GraphQLObjectType, None], Field, GraphQLField]]]
):
    # type: (...) -> None
    """Collect all Conflicts "within" one collection of fields."""

    # field map is a keyed collection, where each key represents a response
    # name and the value at that key is a list of all fields which provide that
    # response name. For every response name, if there are multiple fields, they
    # must be compared to find a potential conflict.
    for response_name, fields in list(field_map.items()):
        # This compares every field in the list to every other field in this list
        # (except to itself). If the list only has one item, nothing needs to
        # be compared.
        for i, field in enumerate(fields):
            for other_field in fields[i + 1 :]:
                # within one collection is never mutually exclusive
                conflict = _find_conflict(
                    context,
                    cached_fields_and_fragment_names,
                    compared_fragments,
                    False,
                    response_name,
                    field,
                    other_field,
                )
                if conflict:
                    conflicts.append(conflict)


def _collect_conflicts_between(
    context,  # type: ValidationContext
    conflicts,  # type: List[Tuple[Tuple[str, str], List[Node], List[Node]]]
    cached_fields_and_fragment_names,  # type: Dict[SelectionSet, Tuple[Dict[str, List[Tuple[Union[GraphQLInterfaceType, GraphQLObjectType, None], Field, GraphQLField]]], List[str]]]
    compared_fragments,  # type: PairSet
    parent_fields_are_mutually_exclusive,  # type: bool
    field_map1,  # type: Dict[str, List[Tuple[Union[GraphQLInterfaceType, GraphQLObjectType, None], Field, GraphQLField]]]
    field_map2,  # type: Dict[str, List[Tuple[Union[GraphQLInterfaceType, GraphQLObjectType, None], Field, GraphQLField]]]
):
    # type: (...) -> None
    """Collect all Conflicts between two collections of fields.

       This is similar to, but different from the `collect_conflicts_within` function above. This check assumes that
       `collect_conflicts_within` has already been called on each provided collection of fields.
       This is true because this validator traverses each individual selection set.
    """
    # A field map is a keyed collection, where each key represents a response
    # name and the value at that key is a list of all fields which provide that
    # response name. For any response name which appears in both provided field
    # maps, each field from the first field map must be compared to every field
    # in the second field map to find potential conflicts.
    for response_name, fields1 in list(field_map1.items()):
        fields2 = field_map2.get(response_name)

        if fields2:
            for field1 in fields1:
                for field2 in fields2:
                    conflict = _find_conflict(
                        context,
                        cached_fields_and_fragment_names,
                        compared_fragments,
                        parent_fields_are_mutually_exclusive,
                        response_name,
                        field1,
                        field2,
                    )

                    if conflict:
                        conflicts.append(conflict)


def _find_conflict(
    context,  # type: ValidationContext
    cached_fields_and_fragment_names,  # type: Dict[SelectionSet, Tuple[Dict[str, List[Tuple[Union[GraphQLInterfaceType, GraphQLObjectType, None], Field, GraphQLField]]], List[str]]]
    compared_fragments,  # type: PairSet
    parent_fields_are_mutually_exclusive,  # type: bool
    response_name,  # type: str
    field1,  # type: Tuple[Union[GraphQLInterfaceType, GraphQLObjectType, None], Field, GraphQLField]
    field2,  # type: Tuple[Union[GraphQLInterfaceType, GraphQLObjectType, None], Field, GraphQLField]
):
    # type: (...) -> Optional[Tuple[Tuple[str, str], List[Node], List[Node]]]
    """Determines if there is a conflict between two particular fields."""
    parent_type1, ast1, def1 = field1
    parent_type2, ast2, def2 = field2

    # If it is known that two fields could not possibly apply at the same
    # time, due to the parent types, then it is safe to permit them to diverge
    # in aliased field or arguments used as they will not present any ambiguity
    # by differing.
    # It is known that two parent types could never overlap if they are
    # different Object types. Interface or Union types might overlap - if not
    # in the current state of the schema, then perhaps in some future version,
    # thus may not safely diverge.

    are_mutually_exclusive = parent_fields_are_mutually_exclusive or (
        parent_type1 != parent_type2
        and isinstance(parent_type1, GraphQLObjectType)
        and isinstance(parent_type2, GraphQLObjectType)
    )

    # The return type for each field.
    type1 = def1 and def1.type
    type2 = def2 and def2.type

    if not are_mutually_exclusive:
        # Two aliases must refer to the same field.
        name1 = ast1.name.value
        name2 = ast2.name.value

        if name1 != name2:
            return (
                (response_name, "{} and {} are different fields".format(name1, name2)),
                [ast1],
                [ast2],
            )

        # Two field calls must have the same arguments.
        if not _same_arguments(ast1.arguments, ast2.arguments):
            return ((response_name, "they have differing arguments"), [ast1], [ast2])

    if type1 and type2 and do_types_conflict(type1, type2):
        return (
            (
                response_name,
                "they return conflicting types {} and {}".format(type1, type2),
            ),
            [ast1],
            [ast2],
        )

    #  Collect and compare sub-fields. Use the same "visited fragment names" list
    # for both collections so fields in a fragment reference are never
    # compared to themselves.
    selection_set1 = ast1.selection_set
    selection_set2 = ast2.selection_set

    if selection_set1 and selection_set2:
        conflicts = _find_conflicts_between_sub_selection_sets(  # type: ignore
            context,
            cached_fields_and_fragment_names,
            compared_fragments,
            are_mutually_exclusive,
            get_named_type(type1),  # type: ignore
            selection_set1,
            get_named_type(type2),  # type: ignore
            selection_set2,
        )

        return _subfield_conflicts(conflicts, response_name, ast1, ast2)

    return None


def _get_fields_and_fragments_names(
    context,  # type: ValidationContext
    cached_fields_and_fragment_names,  # type: Dict[SelectionSet, Tuple[Dict[str, List[Tuple[Union[GraphQLInterfaceType, GraphQLObjectType, None], Field, GraphQLField]]], List[str]]]
    parent_type,  # type: Union[GraphQLInterfaceType, GraphQLObjectType, None]
    selection_set,  # type: SelectionSet
):
    # type: (...) -> Tuple[Dict[str, List[Tuple[Union[GraphQLInterfaceType, GraphQLObjectType, None], Field, GraphQLField]]], List[str]]
    cached = cached_fields_and_fragment_names.get(selection_set)

    if not cached:
        ast_and_defs = (
            OrderedDict()
        )  # type: Dict[str, List[Tuple[Union[GraphQLInterfaceType, GraphQLObjectType, None], Field, GraphQLField]]]
        fragment_names = OrderedDict()  # type: Dict[str, bool]
        _collect_fields_and_fragment_names(
            context, parent_type, selection_set, ast_and_defs, fragment_names
        )
        cached = (ast_and_defs, list(fragment_names.keys()))
        cached_fields_and_fragment_names[selection_set] = cached

    return cached


def _get_referenced_fields_and_fragment_names(
    context,  # ValidationContext
    cached_fields_and_fragment_names,  # type: Dict[SelectionSet, Tuple[Dict[str, List[Tuple[Union[GraphQLInterfaceType, GraphQLObjectType, None], Field, GraphQLField]]], List[str]]]
    fragment,  # type: InlineFragment
):
    # type: (...) -> Tuple[Dict[str, List[Tuple[Union[GraphQLInterfaceType, GraphQLObjectType, None], Field, GraphQLField]]], List[str]]
    """Given a reference to a fragment, return the represented collection of fields as well as a list of
    nested fragment names referenced via fragment spreads."""

    # Short-circuit building a type from the AST if possible.
    cached = cached_fields_and_fragment_names.get(fragment.selection_set)

    if cached:
        return cached

    fragment_type = type_from_ast(  # type: ignore
        context.get_schema(), fragment.type_condition
    )

    return _get_fields_and_fragments_names(  # type: ignore
        context, cached_fields_and_fragment_names, fragment_type, fragment.selection_set
    )


def _collect_fields_and_fragment_names(
    context,  # type: ValidationContext
    parent_type,  # type: Union[GraphQLInterfaceType, GraphQLObjectType, None]
    selection_set,  # type: SelectionSet
    ast_and_defs,  # type: Dict[str, List[Tuple[Union[GraphQLInterfaceType, GraphQLObjectType, None], Field, GraphQLField]]]
    fragment_names,  # type: Dict[str, bool]
):
    # type: (...) -> None

    for selection in selection_set.selections:
        if isinstance(selection, ast.Field):
            field_name = selection.name.value
            if isinstance(parent_type, (GraphQLObjectType, GraphQLInterfaceType)):
                field_def = parent_type.fields.get(field_name)
            else:
                field_def = None

            response_name = selection.alias.value if selection.alias else field_name

            if not ast_and_defs.get(response_name):
                ast_and_defs[response_name] = []  # type: ignore

            ast_and_defs[response_name].append((parent_type, selection, field_def))

        elif isinstance(selection, ast.FragmentSpread):
            fragment_names[selection.name.value] = True
        elif isinstance(selection, ast.InlineFragment):
            type_condition = selection.type_condition
            if type_condition:
                inline_fragment_type = type_from_ast(  # type: ignore
                    context.get_schema(), selection.type_condition
                )
            else:
                inline_fragment_type = parent_type  # type: ignore

            _collect_fields_and_fragment_names(  # type: ignore
                context,
                inline_fragment_type,
                selection.selection_set,
                ast_and_defs,
                fragment_names,
            )


def _subfield_conflicts(
    conflicts,  # type: List[Tuple[Tuple[str, str], List[Node], List[Node]]]
    response_name,  # type: str
    ast1,  # type: Node
    ast2,  # type: Node
):
    # type: (...) -> Optional[Tuple[Tuple[str, str], List[Node], List[Node]]]
    """Given a series of Conflicts which occurred between two sub-fields, generate a single Conflict."""
    if conflicts:
        return (  # type: ignore
            (response_name, [conflict[0] for conflict in conflicts]),
            tuple(itertools.chain([ast1], *[conflict[1] for conflict in conflicts])),
            tuple(itertools.chain([ast2], *[conflict[2] for conflict in conflicts])),
        )
    return None


def do_types_conflict(type1, type2):
    # type: (GraphQLScalarType, GraphQLScalarType) -> bool
    if isinstance(type1, GraphQLList):
        if isinstance(type2, GraphQLList):
            return do_types_conflict(type1.of_type, type2.of_type)
        return True

    if isinstance(type2, GraphQLList):
        if isinstance(type1, GraphQLList):
            return do_types_conflict(type1.of_type, type2.of_type)
        return True

    if isinstance(type1, GraphQLNonNull):
        if isinstance(type2, GraphQLNonNull):
            return do_types_conflict(type1.of_type, type2.of_type)
        return True

    if isinstance(type2, GraphQLNonNull):
        if isinstance(type1, GraphQLNonNull):
            return do_types_conflict(type1.of_type, type2.of_type)
        return True

    if is_leaf_type(type1) or is_leaf_type(type2):
        return type1 != type2

    return False


def _same_value(value1, value2):
    # type: (Optional[Node], Optional[Node]) -> bool
    if not value1 and not value2:
        return True
    if not value1 or not value2:
        return False
    return print_ast(value1) == print_ast(value2)


def _same_arguments(arguments1, arguments2):
    # type: (Optional[List[Argument]], Optional[List[Argument]]) -> bool
    # Check to see if they are empty arguments or nones. If they are, we can
    # bail out early.
    if not arguments1 and not arguments2:
        return True

    if not arguments1:
        return False

    if not arguments2:
        return False

    if len(arguments1) != len(arguments2):
        return False

    arguments2_values_to_arg = {a.name.value: a for a in arguments2}

    for argument1 in arguments1:
        argument2 = arguments2_values_to_arg.get(argument1.name.value)
        if not argument2:
            return False

        if not _same_value(argument1.value, argument2.value):
            return False

    return True

from graphql.language.ast import (
    Document,
    Field,
    Name,
    OperationDefinition,
    SelectionSet,
)
from graphql.language.parser import parse
from graphql.language.printer import print_ast
from graphql.language.visitor import (
    BREAK,
    REMOVE,
    ParallelVisitor,
    TypeInfoVisitor,
    Visitor,
    visit,
)
from graphql.type import get_named_type, is_composite_type
from graphql.utils.type_info import TypeInfo

from ...validation.tests.utils import test_schema
from .fixtures import KITCHEN_SINK
from graphql.language.ast import Document
from graphql.language.ast import OperationDefinition
from graphql.language.ast import SelectionSet
from typing import Any
from typing import Optional
from typing import Union
from graphql.language.ast import Field
from graphql.language.ast import Name
from graphql.language.visitor import _Falsey
from typing import List
from graphql.language.ast import Argument
from graphql.language.ast import IntValue


def test_allows_editing_a_node_both_on_enter_and_on_leave():
    # type: () -> None
    ast = parse("{ a, b, c { a, b, c } }", no_location=True)

    class TestVisitor(Visitor):
        def __init__(self):
            # type: () -> None
            self.did_enter = False
            self.did_leave = False

        def enter(
            self,
            node,  # type: Union[Document, OperationDefinition, SelectionSet]
            *args  # type: Any
        ):
            # type: (...) -> Optional[OperationDefinition]
            if isinstance(node, OperationDefinition):
                self.did_enter = True
                selection_set = node.selection_set
                self.selections = None
                if selection_set:
                    self.selections = selection_set.selections
                new_selection_set = SelectionSet(selections=[])
                return OperationDefinition(
                    name=node.name,
                    variable_definitions=node.variable_definitions,
                    directives=node.directives,
                    loc=node.loc,
                    operation=node.operation,
                    selection_set=new_selection_set,
                )

        def leave(
            self,
            node,  # type: Union[Document, OperationDefinition, SelectionSet]
            *args  # type: Any
        ):
            # type: (...) -> Optional[OperationDefinition]
            if isinstance(node, OperationDefinition):
                self.did_leave = True
                new_selection_set = None
                if self.selections:
                    new_selection_set = SelectionSet(selections=self.selections)
                return OperationDefinition(
                    name=node.name,
                    variable_definitions=node.variable_definitions,
                    directives=node.directives,
                    loc=node.loc,
                    operation=node.operation,
                    selection_set=new_selection_set,
                )

    visitor = TestVisitor()
    edited_ast = visit(ast, visitor)
    assert ast == parse("{ a, b, c { a, b, c } }", no_location=True)
    assert edited_ast == ast
    assert visitor.did_enter
    assert visitor.did_leave


def test_allows_editing_the_root_node_on_enter_and_on_leave():
    # type: () -> None
    ast = parse("{ a, b, c { a, b, c } }", no_location=True)

    definitions = ast.definitions

    class TestVisitor(Visitor):
        def __init__(self):
            # type: () -> None
            self.did_enter = False
            self.did_leave = False

        def enter(self, node, *args):
            # type: (Document, *Any) -> Document
            if isinstance(node, Document):
                self.did_enter = True
                return Document(loc=node.loc, definitions=[])

        def leave(self, node, *args):
            # type: (Document, *Any) -> Document
            if isinstance(node, Document):
                self.did_leave = True
                return Document(loc=node.loc, definitions=definitions)

    visitor = TestVisitor()
    edited_ast = visit(ast, visitor)
    assert edited_ast == ast
    assert visitor.did_enter
    assert visitor.did_leave


def test_allows_for_editing_on_enter():
    # type: () -> None
    ast = parse("{ a, b, c { a, b, c } }", no_location=True)

    class TestVisitor(Visitor):
        def enter(self, node, *args):
            # type: (Any, *Any) -> Optional[Any]
            if isinstance(node, Field) and node.name.value == "b":
                return REMOVE

    edited_ast = visit(ast, TestVisitor())

    assert ast == parse("{ a, b, c { a, b, c } }", no_location=True)
    assert edited_ast == parse("{ a,   c { a,   c } }", no_location=True)


def test_allows_for_editing_on_leave():
    # type: () -> None
    ast = parse("{ a, b, c { a, b, c } }", no_location=True)

    class TestVisitor(Visitor):
        def leave(self, node, *args):
            # type: (Union[Field, Name], *Any) -> Optional[Falsey]
            if isinstance(node, Field) and node.name.value == "b":
                return REMOVE

    edited_ast = visit(ast, TestVisitor())

    assert ast == parse("{ a, b, c { a, b, c } }", no_location=True)
    assert edited_ast == parse("{ a,   c { a,   c } }", no_location=True)


def test_visits_edited_node():
    # type: () -> None
    added_field = Field(name=Name(value="__typename"))
    ast = parse("{ a { x } }")

    class TestVisitor(Visitor):
        def __init__(self):
            # type: () -> None
            self.did_visit_added_field = False

        def enter(self, node, *args):
            # type: (Any, *Any) -> Optional[Field]
            if isinstance(node, Field) and node.name.value == "a":
                selection_set = node.selection_set
                selections = []
                if selection_set:
                    selections = selection_set.selections
                new_selection_set = SelectionSet(selections=[added_field] + selections)
                return Field(name=None, selection_set=new_selection_set)
            if node is added_field:
                self.did_visit_added_field = True

    visitor = TestVisitor()
    visit(ast, visitor)
    assert visitor.did_visit_added_field


def test_allows_skipping_a_subtree():
    # type: () -> None
    visited = []
    ast = parse("{ a, b { x }, c }")

    class TestVisitor(Visitor):
        def enter(self, node, *args):
            # type: (Any, *Any) -> Optional[Any]
            visited.append(["enter", type(node).__name__, getattr(node, "value", None)])
            if isinstance(node, Field) and node.name.value == "b":
                return False

        def leave(self, node, *args):
            # type: (Union[Field, Name, SelectionSet], *Any) -> None
            visited.append(["leave", type(node).__name__, getattr(node, "value", None)])

    visit(ast, TestVisitor())

    assert visited == [
        ["enter", "Document", None],
        ["enter", "OperationDefinition", None],
        ["enter", "SelectionSet", None],
        ["enter", "Field", None],
        ["enter", "Name", "a"],
        ["leave", "Name", "a"],
        ["leave", "Field", None],
        ["enter", "Field", None],
        ["enter", "Field", None],
        ["enter", "Name", "c"],
        ["leave", "Name", "c"],
        ["leave", "Field", None],
        ["leave", "SelectionSet", None],
        ["leave", "OperationDefinition", None],
        ["leave", "Document", None],
    ]


def test_allows_early_exit_while_visiting():
    # type: () -> None
    visited = []
    ast = parse("{ a, b { x }, c }")

    class TestVisitor(Visitor):
        def enter(self, node, *args):
            # type: (Any, *Any) -> Optional[Any]
            visited.append(["enter", type(node).__name__, getattr(node, "value", None)])
            if isinstance(node, Name) and node.value == "x":
                return BREAK

        def leave(self, node, *args):
            # type: (Union[Field, Name], *Any) -> None
            visited.append(["leave", type(node).__name__, getattr(node, "value", None)])

    visit(ast, TestVisitor())

    assert visited == [
        ["enter", "Document", None],
        ["enter", "OperationDefinition", None],
        ["enter", "SelectionSet", None],
        ["enter", "Field", None],
        ["enter", "Name", "a"],
        ["leave", "Name", "a"],
        ["leave", "Field", None],
        ["enter", "Field", None],
        ["enter", "Name", "b"],
        ["leave", "Name", "b"],
        ["enter", "SelectionSet", None],
        ["enter", "Field", None],
        ["enter", "Name", "x"],
    ]


def test_allows_a_named_functions_visitor_api():
    # type: () -> None
    visited = []
    ast = parse("{ a, b { x }, c }")

    class TestVisitor(Visitor):
        def enter_Name(self, node, *args):
            # type: (Name, *Any) -> None
            visited.append(["enter", type(node).__name__, getattr(node, "value", None)])

        def enter_SelectionSet(self, node, *args):
            # type: (SelectionSet, *Any) -> None
            visited.append(["enter", type(node).__name__, getattr(node, "value", None)])

        def leave_SelectionSet(self, node, *args):
            # type: (SelectionSet, *Any) -> None
            visited.append(["leave", type(node).__name__, getattr(node, "value", None)])

    visit(ast, TestVisitor())

    assert visited == [
        ["enter", "SelectionSet", None],
        ["enter", "Name", "a"],
        ["enter", "Name", "b"],
        ["enter", "SelectionSet", None],
        ["enter", "Name", "x"],
        ["leave", "SelectionSet", None],
        ["enter", "Name", "c"],
        ["leave", "SelectionSet", None],
    ]


def test_visits_kitchen_sink():
    # type: () -> None
    visited = []
    ast = parse(KITCHEN_SINK)

    class TestVisitor(Visitor):
        def enter(self, node, key, parent, *args):
            # type: (Any, Union[None, int, str], Any, *List[Any]) -> None
            kind = parent and type(parent).__name__
            if kind == "list":
                kind = None
            visited.append(["enter", type(node).__name__, key, kind])

        def leave(self, node, key, parent, *args):
            # type: (Any, Union[int, str], Any, *List[Any]) -> None
            kind = parent and type(parent).__name__
            if kind == "list":
                kind = None
            visited.append(["leave", type(node).__name__, key, kind])

    visit(ast, TestVisitor())
    assert visited == [
        ["enter", "Document", None, None],
        ["enter", "OperationDefinition", 0, None],
        ["enter", "Name", "name", "OperationDefinition"],
        ["leave", "Name", "name", "OperationDefinition"],
        ["enter", "VariableDefinition", 0, None],
        ["enter", "Variable", "variable", "VariableDefinition"],
        ["enter", "Name", "name", "Variable"],
        ["leave", "Name", "name", "Variable"],
        ["leave", "Variable", "variable", "VariableDefinition"],
        ["enter", "NamedType", "type", "VariableDefinition"],
        ["enter", "Name", "name", "NamedType"],
        ["leave", "Name", "name", "NamedType"],
        ["leave", "NamedType", "type", "VariableDefinition"],
        ["leave", "VariableDefinition", 0, None],
        ["enter", "VariableDefinition", 1, None],
        ["enter", "Variable", "variable", "VariableDefinition"],
        ["enter", "Name", "name", "Variable"],
        ["leave", "Name", "name", "Variable"],
        ["leave", "Variable", "variable", "VariableDefinition"],
        ["enter", "NamedType", "type", "VariableDefinition"],
        ["enter", "Name", "name", "NamedType"],
        ["leave", "Name", "name", "NamedType"],
        ["leave", "NamedType", "type", "VariableDefinition"],
        ["enter", "EnumValue", "default_value", "VariableDefinition"],
        ["leave", "EnumValue", "default_value", "VariableDefinition"],
        ["leave", "VariableDefinition", 1, None],
        ["enter", "SelectionSet", "selection_set", "OperationDefinition"],
        ["enter", "Field", 0, None],
        ["enter", "Name", "alias", "Field"],
        ["leave", "Name", "alias", "Field"],
        ["enter", "Name", "name", "Field"],
        ["leave", "Name", "name", "Field"],
        ["enter", "Argument", 0, None],
        ["enter", "Name", "name", "Argument"],
        ["leave", "Name", "name", "Argument"],
        ["enter", "ListValue", "value", "Argument"],
        ["enter", "IntValue", 0, None],
        ["leave", "IntValue", 0, None],
        ["enter", "IntValue", 1, None],
        ["leave", "IntValue", 1, None],
        ["leave", "ListValue", "value", "Argument"],
        ["leave", "Argument", 0, None],
        ["enter", "SelectionSet", "selection_set", "Field"],
        ["enter", "Field", 0, None],
        ["enter", "Name", "name", "Field"],
        ["leave", "Name", "name", "Field"],
        ["leave", "Field", 0, None],
        ["enter", "InlineFragment", 1, None],
        ["enter", "NamedType", "type_condition", "InlineFragment"],
        ["enter", "Name", "name", "NamedType"],
        ["leave", "Name", "name", "NamedType"],
        ["leave", "NamedType", "type_condition", "InlineFragment"],
        ["enter", "Directive", 0, None],
        ["enter", "Name", "name", "Directive"],
        ["leave", "Name", "name", "Directive"],
        ["leave", "Directive", 0, None],
        ["enter", "SelectionSet", "selection_set", "InlineFragment"],
        ["enter", "Field", 0, None],
        ["enter", "Name", "name", "Field"],
        ["leave", "Name", "name", "Field"],
        ["enter", "SelectionSet", "selection_set", "Field"],
        ["enter", "Field", 0, None],
        ["enter", "Name", "name", "Field"],
        ["leave", "Name", "name", "Field"],
        ["leave", "Field", 0, None],
        ["enter", "Field", 1, None],
        ["enter", "Name", "alias", "Field"],
        ["leave", "Name", "alias", "Field"],
        ["enter", "Name", "name", "Field"],
        ["leave", "Name", "name", "Field"],
        ["enter", "Argument", 0, None],
        ["enter", "Name", "name", "Argument"],
        ["leave", "Name", "name", "Argument"],
        ["enter", "IntValue", "value", "Argument"],
        ["leave", "IntValue", "value", "Argument"],
        ["leave", "Argument", 0, None],
        ["enter", "Argument", 1, None],
        ["enter", "Name", "name", "Argument"],
        ["leave", "Name", "name", "Argument"],
        ["enter", "Variable", "value", "Argument"],
        ["enter", "Name", "name", "Variable"],
        ["leave", "Name", "name", "Variable"],
        ["leave", "Variable", "value", "Argument"],
        ["leave", "Argument", 1, None],
        ["enter", "Directive", 0, None],
        ["enter", "Name", "name", "Directive"],
        ["leave", "Name", "name", "Directive"],
        ["enter", "Argument", 0, None],
        ["enter", "Name", "name", "Argument"],
        ["leave", "Name", "name", "Argument"],
        ["enter", "Variable", "value", "Argument"],
        ["enter", "Name", "name", "Variable"],
        ["leave", "Name", "name", "Variable"],
        ["leave", "Variable", "value", "Argument"],
        ["leave", "Argument", 0, None],
        ["leave", "Directive", 0, None],
        ["enter", "SelectionSet", "selection_set", "Field"],
        ["enter", "Field", 0, None],
        ["enter", "Name", "name", "Field"],
        ["leave", "Name", "name", "Field"],
        ["leave", "Field", 0, None],
        ["enter", "FragmentSpread", 1, None],
        ["enter", "Name", "name", "FragmentSpread"],
        ["leave", "Name", "name", "FragmentSpread"],
        ["leave", "FragmentSpread", 1, None],
        ["leave", "SelectionSet", "selection_set", "Field"],
        ["leave", "Field", 1, None],
        ["leave", "SelectionSet", "selection_set", "Field"],
        ["leave", "Field", 0, None],
        ["leave", "SelectionSet", "selection_set", "InlineFragment"],
        ["leave", "InlineFragment", 1, None],
        ["enter", "InlineFragment", 2, None],
        ["enter", "Directive", 0, None],
        ["enter", "Name", "name", "Directive"],
        ["leave", "Name", "name", "Directive"],
        ["enter", "Argument", 0, None],
        ["enter", "Name", "name", "Argument"],
        ["leave", "Name", "name", "Argument"],
        ["enter", "Variable", "value", "Argument"],
        ["enter", "Name", "name", "Variable"],
        ["leave", "Name", "name", "Variable"],
        ["leave", "Variable", "value", "Argument"],
        ["leave", "Argument", 0, None],
        ["leave", "Directive", 0, None],
        ["enter", "SelectionSet", "selection_set", "InlineFragment"],
        ["enter", "Field", 0, None],
        ["enter", "Name", "name", "Field"],
        ["leave", "Name", "name", "Field"],
        ["leave", "Field", 0, None],
        ["leave", "SelectionSet", "selection_set", "InlineFragment"],
        ["leave", "InlineFragment", 2, None],
        ["enter", "InlineFragment", 3, None],
        ["enter", "SelectionSet", "selection_set", "InlineFragment"],
        ["enter", "Field", 0, None],
        ["enter", "Name", "name", "Field"],
        ["leave", "Name", "name", "Field"],
        ["leave", "Field", 0, None],
        ["leave", "SelectionSet", "selection_set", "InlineFragment"],
        ["leave", "InlineFragment", 3, None],
        ["leave", "SelectionSet", "selection_set", "Field"],
        ["leave", "Field", 0, None],
        ["leave", "SelectionSet", "selection_set", "OperationDefinition"],
        ["leave", "OperationDefinition", 0, None],
        ["enter", "OperationDefinition", 1, None],
        ["enter", "Name", "name", "OperationDefinition"],
        ["leave", "Name", "name", "OperationDefinition"],
        ["enter", "SelectionSet", "selection_set", "OperationDefinition"],
        ["enter", "Field", 0, None],
        ["enter", "Name", "name", "Field"],
        ["leave", "Name", "name", "Field"],
        ["enter", "Argument", 0, None],
        ["enter", "Name", "name", "Argument"],
        ["leave", "Name", "name", "Argument"],
        ["enter", "IntValue", "value", "Argument"],
        ["leave", "IntValue", "value", "Argument"],
        ["leave", "Argument", 0, None],
        ["enter", "Directive", 0, None],
        ["enter", "Name", "name", "Directive"],
        ["leave", "Name", "name", "Directive"],
        ["leave", "Directive", 0, None],
        ["enter", "SelectionSet", "selection_set", "Field"],
        ["enter", "Field", 0, None],
        ["enter", "Name", "name", "Field"],
        ["leave", "Name", "name", "Field"],
        ["enter", "SelectionSet", "selection_set", "Field"],
        ["enter", "Field", 0, None],
        ["enter", "Name", "name", "Field"],
        ["leave", "Name", "name", "Field"],
        ["leave", "Field", 0, None],
        ["leave", "SelectionSet", "selection_set", "Field"],
        ["leave", "Field", 0, None],
        ["leave", "SelectionSet", "selection_set", "Field"],
        ["leave", "Field", 0, None],
        ["leave", "SelectionSet", "selection_set", "OperationDefinition"],
        ["leave", "OperationDefinition", 1, None],
        ["enter", "OperationDefinition", 2, None],
        ["enter", "Name", "name", "OperationDefinition"],
        ["leave", "Name", "name", "OperationDefinition"],
        ["enter", "VariableDefinition", 0, None],
        ["enter", "Variable", "variable", "VariableDefinition"],
        ["enter", "Name", "name", "Variable"],
        ["leave", "Name", "name", "Variable"],
        ["leave", "Variable", "variable", "VariableDefinition"],
        ["enter", "NamedType", "type", "VariableDefinition"],
        ["enter", "Name", "name", "NamedType"],
        ["leave", "Name", "name", "NamedType"],
        ["leave", "NamedType", "type", "VariableDefinition"],
        ["leave", "VariableDefinition", 0, None],
        ["enter", "SelectionSet", "selection_set", "OperationDefinition"],
        ["enter", "Field", 0, None],
        ["enter", "Name", "name", "Field"],
        ["leave", "Name", "name", "Field"],
        ["enter", "Argument", 0, None],
        ["enter", "Name", "name", "Argument"],
        ["leave", "Name", "name", "Argument"],
        ["enter", "Variable", "value", "Argument"],
        ["enter", "Name", "name", "Variable"],
        ["leave", "Name", "name", "Variable"],
        ["leave", "Variable", "value", "Argument"],
        ["leave", "Argument", 0, None],
        ["enter", "SelectionSet", "selection_set", "Field"],
        ["enter", "Field", 0, None],
        ["enter", "Name", "name", "Field"],
        ["leave", "Name", "name", "Field"],
        ["enter", "SelectionSet", "selection_set", "Field"],
        ["enter", "Field", 0, None],
        ["enter", "Name", "name", "Field"],
        ["leave", "Name", "name", "Field"],
        ["enter", "SelectionSet", "selection_set", "Field"],
        ["enter", "Field", 0, None],
        ["enter", "Name", "name", "Field"],
        ["leave", "Name", "name", "Field"],
        ["leave", "Field", 0, None],
        ["leave", "SelectionSet", "selection_set", "Field"],
        ["leave", "Field", 0, None],
        ["enter", "Field", 1, None],
        ["enter", "Name", "name", "Field"],
        ["leave", "Name", "name", "Field"],
        ["enter", "SelectionSet", "selection_set", "Field"],
        ["enter", "Field", 0, None],
        ["enter", "Name", "name", "Field"],
        ["leave", "Name", "name", "Field"],
        ["leave", "Field", 0, None],
        ["leave", "SelectionSet", "selection_set", "Field"],
        ["leave", "Field", 1, None],
        ["leave", "SelectionSet", "selection_set", "Field"],
        ["leave", "Field", 0, None],
        ["leave", "SelectionSet", "selection_set", "Field"],
        ["leave", "Field", 0, None],
        ["leave", "SelectionSet", "selection_set", "OperationDefinition"],
        ["leave", "OperationDefinition", 2, None],
        ["enter", "FragmentDefinition", 3, None],
        ["enter", "Name", "name", "FragmentDefinition"],
        ["leave", "Name", "name", "FragmentDefinition"],
        ["enter", "NamedType", "type_condition", "FragmentDefinition"],
        ["enter", "Name", "name", "NamedType"],
        ["leave", "Name", "name", "NamedType"],
        ["leave", "NamedType", "type_condition", "FragmentDefinition"],
        ["enter", "SelectionSet", "selection_set", "FragmentDefinition"],
        ["enter", "Field", 0, None],
        ["enter", "Name", "name", "Field"],
        ["leave", "Name", "name", "Field"],
        ["enter", "Argument", 0, None],
        ["enter", "Name", "name", "Argument"],
        ["leave", "Name", "name", "Argument"],
        ["enter", "Variable", "value", "Argument"],
        ["enter", "Name", "name", "Variable"],
        ["leave", "Name", "name", "Variable"],
        ["leave", "Variable", "value", "Argument"],
        ["leave", "Argument", 0, None],
        ["enter", "Argument", 1, None],
        ["enter", "Name", "name", "Argument"],
        ["leave", "Name", "name", "Argument"],
        ["enter", "Variable", "value", "Argument"],
        ["enter", "Name", "name", "Variable"],
        ["leave", "Name", "name", "Variable"],
        ["leave", "Variable", "value", "Argument"],
        ["leave", "Argument", 1, None],
        ["enter", "Argument", 2, None],
        ["enter", "Name", "name", "Argument"],
        ["leave", "Name", "name", "Argument"],
        ["enter", "ObjectValue", "value", "Argument"],
        ["enter", "ObjectField", 0, None],
        ["enter", "Name", "name", "ObjectField"],
        ["leave", "Name", "name", "ObjectField"],
        ["enter", "StringValue", "value", "ObjectField"],
        ["leave", "StringValue", "value", "ObjectField"],
        ["leave", "ObjectField", 0, None],
        ["leave", "ObjectValue", "value", "Argument"],
        ["leave", "Argument", 2, None],
        ["leave", "Field", 0, None],
        ["leave", "SelectionSet", "selection_set", "FragmentDefinition"],
        ["leave", "FragmentDefinition", 3, None],
        ["enter", "OperationDefinition", 4, None],
        ["enter", "SelectionSet", "selection_set", "OperationDefinition"],
        ["enter", "Field", 0, None],
        ["enter", "Name", "name", "Field"],
        ["leave", "Name", "name", "Field"],
        ["enter", "Argument", 0, None],
        ["enter", "Name", "name", "Argument"],
        ["leave", "Name", "name", "Argument"],
        ["enter", "BooleanValue", "value", "Argument"],
        ["leave", "BooleanValue", "value", "Argument"],
        ["leave", "Argument", 0, None],
        ["enter", "Argument", 1, None],
        ["enter", "Name", "name", "Argument"],
        ["leave", "Name", "name", "Argument"],
        ["enter", "BooleanValue", "value", "Argument"],
        ["leave", "BooleanValue", "value", "Argument"],
        ["leave", "Argument", 1, None],
        ["leave", "Field", 0, None],
        ["enter", "Field", 1, None],
        ["enter", "Name", "name", "Field"],
        ["leave", "Name", "name", "Field"],
        ["leave", "Field", 1, None],
        ["leave", "SelectionSet", "selection_set", "OperationDefinition"],
        ["leave", "OperationDefinition", 4, None],
        ["leave", "Document", None, None],
    ]


def test_visits_in_pararell_allows_skipping_a_subtree():
    # type: () -> None
    visited = []
    ast = parse("{ a, b { x }, c }")

    class TestVisitor(Visitor):
        def enter(self, node, key, parent, *args):
            # type: (Any, Union[None, int, str], Any, *List[Any]) -> Optional[Any]
            visited.append(["enter", type(node).__name__, getattr(node, "value", None)])
            if type(node).__name__ == "Field" and node.name.value == "b":
                return False

        def leave(
            self,
            node,  # type: Union[Field, Name, SelectionSet]
            key,  # type: Union[int, str]
            parent,  # type: Union[List[Field], Field, OperationDefinition]
            *args  # type: List[Any]
        ):
            # type: (...) -> None
            visited.append(["leave", type(node).__name__, getattr(node, "value", None)])

    visit(ast, ParallelVisitor([TestVisitor()]))
    assert visited == [
        ["enter", "Document", None],
        ["enter", "OperationDefinition", None],
        ["enter", "SelectionSet", None],
        ["enter", "Field", None],
        ["enter", "Name", "a"],
        ["leave", "Name", "a"],
        ["leave", "Field", None],
        ["enter", "Field", None],
        ["enter", "Field", None],
        ["enter", "Name", "c"],
        ["leave", "Name", "c"],
        ["leave", "Field", None],
        ["leave", "SelectionSet", None],
        ["leave", "OperationDefinition", None],
        ["leave", "Document", None],
    ]


def test_visits_in_pararell_allows_skipping_different_subtrees():
    # type: () -> None
    visited = []
    ast = parse("{ a { x }, b { y} }")

    class TestVisitor(Visitor):
        def __init__(self, name):
            # type: (str) -> None
            self.name = name

        def enter(
            self,
            node,  # type: Union[Document, OperationDefinition, SelectionSet]
            key,  # type: Union[None, int, str]
            parent,  # type: Union[List[OperationDefinition], None, OperationDefinition]
            *args  # type: Any
        ):
            # type: (...) -> Optional[Any]
            visited.append(
                [
                    "no-{}".format(self.name),
                    "enter",
                    type(node).__name__,
                    getattr(node, "value", None),
                ]
            )
            if type(node).__name__ == "Field" and node.name.value == self.name:
                return False

        def leave(
            self,
            node,  # type: Union[Field, Name, SelectionSet]
            key,  # type: Union[int, str]
            parent,  # type: Union[List[Field], Field]
            *args  # type: List[Any]
        ):
            # type: (...) -> None
            visited.append(
                [
                    "no-{}".format(self.name),
                    "leave",
                    type(node).__name__,
                    getattr(node, "value", None),
                ]
            )

    visit(ast, ParallelVisitor([TestVisitor("a"), TestVisitor("b")]))
    assert visited == [
        ["no-a", "enter", "Document", None],
        ["no-b", "enter", "Document", None],
        ["no-a", "enter", "OperationDefinition", None],
        ["no-b", "enter", "OperationDefinition", None],
        ["no-a", "enter", "SelectionSet", None],
        ["no-b", "enter", "SelectionSet", None],
        ["no-a", "enter", "Field", None],
        ["no-b", "enter", "Field", None],
        ["no-b", "enter", "Name", "a"],
        ["no-b", "leave", "Name", "a"],
        ["no-b", "enter", "SelectionSet", None],
        ["no-b", "enter", "Field", None],
        ["no-b", "enter", "Name", "x"],
        ["no-b", "leave", "Name", "x"],
        ["no-b", "leave", "Field", None],
        ["no-b", "leave", "SelectionSet", None],
        ["no-b", "leave", "Field", None],
        ["no-a", "enter", "Field", None],
        ["no-b", "enter", "Field", None],
        ["no-a", "enter", "Name", "b"],
        ["no-a", "leave", "Name", "b"],
        ["no-a", "enter", "SelectionSet", None],
        ["no-a", "enter", "Field", None],
        ["no-a", "enter", "Name", "y"],
        ["no-a", "leave", "Name", "y"],
        ["no-a", "leave", "Field", None],
        ["no-a", "leave", "SelectionSet", None],
        ["no-a", "leave", "Field", None],
        ["no-a", "leave", "SelectionSet", None],
        ["no-b", "leave", "SelectionSet", None],
        ["no-a", "leave", "OperationDefinition", None],
        ["no-b", "leave", "OperationDefinition", None],
        ["no-a", "leave", "Document", None],
        ["no-b", "leave", "Document", None],
    ]


def test_visits_in_pararell_allows_early_exit_while_visiting():
    # type: () -> None
    visited = []
    ast = parse("{ a, b { x }, c }")

    class TestVisitor(Visitor):
        def enter(self, node, key, parent, *args):
            # type: (Any, Union[None, int, str], Any, *List[Any]) -> None
            visited.append(["enter", type(node).__name__, getattr(node, "value", None)])

        def leave(
            self,
            node,  # type: Union[Field, Name]
            key,  # type: Union[int, str]
            parent,  # type: Union[List[Field], Field]
            *args  # type: List[Any]
        ):
            # type: (...) -> Optional[object]
            visited.append(["leave", type(node).__name__, getattr(node, "value", None)])
            if type(node).__name__ == "Name" and node.value == "x":
                return BREAK

    visit(ast, ParallelVisitor([TestVisitor()]))
    assert visited == [
        ["enter", "Document", None],
        ["enter", "OperationDefinition", None],
        ["enter", "SelectionSet", None],
        ["enter", "Field", None],
        ["enter", "Name", "a"],
        ["leave", "Name", "a"],
        ["leave", "Field", None],
        ["enter", "Field", None],
        ["enter", "Name", "b"],
        ["leave", "Name", "b"],
        ["enter", "SelectionSet", None],
        ["enter", "Field", None],
        ["enter", "Name", "x"],
        ["leave", "Name", "x"],
    ]


def test_visits_in_pararell_allows_early_exit_from_different_points():
    # type: () -> None
    visited = []
    ast = parse("{ a { y }, b { x } }")

    class TestVisitor(Visitor):
        def __init__(self, name):
            # type: (str) -> None
            self.name = name

        def enter(
            self,
            node,  # type: Union[Document, OperationDefinition, SelectionSet]
            key,  # type: Union[None, int, str]
            parent,  # type: Union[List[OperationDefinition], None, OperationDefinition]
            *args  # type: Any
        ):
            # type: (...) -> None
            visited.append(
                [
                    "break-{}".format(self.name),
                    "enter",
                    type(node).__name__,
                    getattr(node, "value", None),
                ]
            )

        def leave(
            self,
            node,  # type: Union[Field, Name]
            key,  # type: Union[int, str]
            parent,  # type: Union[List[Field], Field]
            *args  # type: List[Any]
        ):
            # type: (...) -> Optional[Any]
            visited.append(
                [
                    "break-{}".format(self.name),
                    "leave",
                    type(node).__name__,
                    getattr(node, "value", None),
                ]
            )
            if type(node).__name__ == "Field" and node.name.value == self.name:
                return BREAK

    visit(ast, ParallelVisitor([TestVisitor("a"), TestVisitor("b")]))
    assert visited == [
        ["break-a", "enter", "Document", None],
        ["break-b", "enter", "Document", None],
        ["break-a", "enter", "OperationDefinition", None],
        ["break-b", "enter", "OperationDefinition", None],
        ["break-a", "enter", "SelectionSet", None],
        ["break-b", "enter", "SelectionSet", None],
        ["break-a", "enter", "Field", None],
        ["break-b", "enter", "Field", None],
        ["break-a", "enter", "Name", "a"],
        ["break-b", "enter", "Name", "a"],
        ["break-a", "leave", "Name", "a"],
        ["break-b", "leave", "Name", "a"],
        ["break-a", "enter", "SelectionSet", None],
        ["break-b", "enter", "SelectionSet", None],
        ["break-a", "enter", "Field", None],
        ["break-b", "enter", "Field", None],
        ["break-a", "enter", "Name", "y"],
        ["break-b", "enter", "Name", "y"],
        ["break-a", "leave", "Name", "y"],
        ["break-b", "leave", "Name", "y"],
        ["break-a", "leave", "Field", None],
        ["break-b", "leave", "Field", None],
        ["break-a", "leave", "SelectionSet", None],
        ["break-b", "leave", "SelectionSet", None],
        ["break-a", "leave", "Field", None],
        ["break-b", "leave", "Field", None],
        ["break-b", "enter", "Field", None],
        ["break-b", "enter", "Name", "b"],
        ["break-b", "leave", "Name", "b"],
        ["break-b", "enter", "SelectionSet", None],
        ["break-b", "enter", "Field", None],
        ["break-b", "enter", "Name", "x"],
        ["break-b", "leave", "Name", "x"],
        ["break-b", "leave", "Field", None],
        ["break-b", "leave", "SelectionSet", None],
        ["break-b", "leave", "Field", None],
    ]


def test_visits_in_pararell_allows_for_editing_on_enter():
    # type: () -> None
    visited = []
    ast = parse("{ a, b, c { a, b, c } }", no_location=True)

    class TestVisitor1(Visitor):
        def enter(self, node, key, parent, *args):
            # type: (Any, Union[None, int, str], Any, *List[Any]) -> Optional[Any]
            if type(node).__name__ == "Field" and node.name.value == "b":
                return REMOVE

    class TestVisitor2(Visitor):
        def enter(self, node, key, parent, *args):
            # type: (Any, Union[None, int, str], Any, *List[Any]) -> None
            visited.append(["enter", type(node).__name__, getattr(node, "value", None)])

        def leave(
            self,
            node,  # type: Union[Field, Name]
            key,  # type: Union[int, str]
            parent,  # type: Union[List[Field], Field]
            *args  # type: List[Any]
        ):
            # type: (...) -> None
            visited.append(["leave", type(node).__name__, getattr(node, "value", None)])

    edited_ast = visit(ast, ParallelVisitor([TestVisitor1(), TestVisitor2()]))

    assert ast == parse("{ a, b, c { a, b, c } }", no_location=True)
    assert edited_ast == parse("{ a,    c { a,    c } }", no_location=True)

    assert visited == [
        ["enter", "Document", None],
        ["enter", "OperationDefinition", None],
        ["enter", "SelectionSet", None],
        ["enter", "Field", None],
        ["enter", "Name", "a"],
        ["leave", "Name", "a"],
        ["leave", "Field", None],
        ["enter", "Field", None],
        ["enter", "Name", "c"],
        ["leave", "Name", "c"],
        ["enter", "SelectionSet", None],
        ["enter", "Field", None],
        ["enter", "Name", "a"],
        ["leave", "Name", "a"],
        ["leave", "Field", None],
        ["enter", "Field", None],
        ["enter", "Name", "c"],
        ["leave", "Name", "c"],
        ["leave", "Field", None],
        ["leave", "SelectionSet", None],
        ["leave", "Field", None],
        ["leave", "SelectionSet", None],
        ["leave", "OperationDefinition", None],
        ["leave", "Document", None],
    ]


def test_visits_in_pararell_allows_for_editing_on_leave():
    # type: () -> None
    visited = []
    ast = parse("{ a, b, c { a, b, c } }", no_location=True)

    class TestVisitor1(Visitor):
        def leave(
            self,
            node,  # type: Union[Field, Name]
            key,  # type: Union[int, str]
            parent,  # type: Union[List[Field], Field]
            *args  # type: List[Any]
        ):
            # type: (...) -> Optional[Falsey]
            if type(node).__name__ == "Field" and node.name.value == "b":
                return REMOVE

    class TestVisitor2(Visitor):
        def enter(self, node, key, parent, *args):
            # type: (Any, Union[None, int, str], Any, *List[Any]) -> None
            visited.append(["enter", type(node).__name__, getattr(node, "value", None)])

        def leave(
            self,
            node,  # type: Union[Field, Name]
            key,  # type: Union[int, str]
            parent,  # type: Union[List[Field], Field]
            *args  # type: List[Any]
        ):
            # type: (...) -> None
            visited.append(["leave", type(node).__name__, getattr(node, "value", None)])

    edited_ast = visit(ast, ParallelVisitor([TestVisitor1(), TestVisitor2()]))

    assert ast == parse("{ a, b, c { a, b, c } }", no_location=True)
    assert edited_ast == parse("{ a,    c { a,    c } }", no_location=True)

    assert visited == [
        ["enter", "Document", None],
        ["enter", "OperationDefinition", None],
        ["enter", "SelectionSet", None],
        ["enter", "Field", None],
        ["enter", "Name", "a"],
        ["leave", "Name", "a"],
        ["leave", "Field", None],
        ["enter", "Field", None],
        ["enter", "Name", "b"],
        ["leave", "Name", "b"],
        ["enter", "Field", None],
        ["enter", "Name", "c"],
        ["leave", "Name", "c"],
        ["enter", "SelectionSet", None],
        ["enter", "Field", None],
        ["enter", "Name", "a"],
        ["leave", "Name", "a"],
        ["leave", "Field", None],
        ["enter", "Field", None],
        ["enter", "Name", "b"],
        ["leave", "Name", "b"],
        ["enter", "Field", None],
        ["enter", "Name", "c"],
        ["leave", "Name", "c"],
        ["leave", "Field", None],
        ["leave", "SelectionSet", None],
        ["leave", "Field", None],
        ["leave", "SelectionSet", None],
        ["leave", "OperationDefinition", None],
        ["leave", "Document", None],
    ]


def test_visits_with_typeinfo_maintains_type_info_during_visit():
    # type: () -> None
    visited = []
    ast = parse("{ human(id: 4) { name, pets { name }, unknown } }")

    type_info = TypeInfo(test_schema)

    class TestVisitor(Visitor):
        def enter(self, node, key, parent, *args):
            # type: (Any, Union[None, int, str], Any, *List[Any]) -> None
            parent_type = type_info.get_parent_type()
            _type = type_info.get_type()
            input_type = type_info.get_input_type()
            visited.append(
                [
                    "enter",
                    type(node).__name__,
                    node.value if type(node).__name__ == "Name" else None,
                    str(parent_type) if parent_type else None,
                    str(_type) if _type else None,
                    str(input_type) if input_type else None,
                ]
            )

        def leave(
            self,
            node,  # type: Union[Argument, IntValue, Name]
            key,  # type: Union[int, str]
            parent,  # type: Union[List[Argument], Argument, Field]
            *args  # type: List[Any]
        ):
            # type: (...) -> None
            parent_type = type_info.get_parent_type()
            _type = type_info.get_type()
            input_type = type_info.get_input_type()
            visited.append(
                [
                    "leave",
                    type(node).__name__,
                    node.value if type(node).__name__ == "Name" else None,
                    str(parent_type) if parent_type else None,
                    str(_type) if _type else None,
                    str(input_type) if input_type else None,
                ]
            )

    visit(ast, TypeInfoVisitor(type_info, TestVisitor()))
    assert visited == [
        ["enter", "Document", None, None, None, None],
        ["enter", "OperationDefinition", None, None, "QueryRoot", None],
        ["enter", "SelectionSet", None, "QueryRoot", "QueryRoot", None],
        ["enter", "Field", None, "QueryRoot", "Human", None],
        ["enter", "Name", "human", "QueryRoot", "Human", None],
        ["leave", "Name", "human", "QueryRoot", "Human", None],
        ["enter", "Argument", None, "QueryRoot", "Human", "ID"],
        ["enter", "Name", "id", "QueryRoot", "Human", "ID"],
        ["leave", "Name", "id", "QueryRoot", "Human", "ID"],
        ["enter", "IntValue", None, "QueryRoot", "Human", "ID"],
        ["leave", "IntValue", None, "QueryRoot", "Human", "ID"],
        ["leave", "Argument", None, "QueryRoot", "Human", "ID"],
        ["enter", "SelectionSet", None, "Human", "Human", None],
        ["enter", "Field", None, "Human", "String", None],
        ["enter", "Name", "name", "Human", "String", None],
        ["leave", "Name", "name", "Human", "String", None],
        ["leave", "Field", None, "Human", "String", None],
        ["enter", "Field", None, "Human", "[Pet]", None],
        ["enter", "Name", "pets", "Human", "[Pet]", None],
        ["leave", "Name", "pets", "Human", "[Pet]", None],
        ["enter", "SelectionSet", None, "Pet", "[Pet]", None],
        ["enter", "Field", None, "Pet", "String", None],
        ["enter", "Name", "name", "Pet", "String", None],
        ["leave", "Name", "name", "Pet", "String", None],
        ["leave", "Field", None, "Pet", "String", None],
        ["leave", "SelectionSet", None, "Pet", "[Pet]", None],
        ["leave", "Field", None, "Human", "[Pet]", None],
        ["enter", "Field", None, "Human", None, None],
        ["enter", "Name", "unknown", "Human", None, None],
        ["leave", "Name", "unknown", "Human", None, None],
        ["leave", "Field", None, "Human", None, None],
        ["leave", "SelectionSet", None, "Human", "Human", None],
        ["leave", "Field", None, "QueryRoot", "Human", None],
        ["leave", "SelectionSet", None, "QueryRoot", "QueryRoot", None],
        ["leave", "OperationDefinition", None, None, "QueryRoot", None],
        ["leave", "Document", None, None, None, None],
    ]


def test_visits_with_typeinfo_maintains_type_info_during_edit():
    # type: () -> None
    visited = []
    ast = parse("{ human(id: 4) { name, pets }, alien }")

    type_info = TypeInfo(test_schema)

    class TestVisitor(Visitor):
        def enter(self, node, key, parent, *args):
            # type: (Any, Union[None, int, str], Any, *List[Any]) -> Optional[Any]
            parent_type = type_info.get_parent_type()
            _type = type_info.get_type()
            input_type = type_info.get_input_type()
            visited.append(
                [
                    "enter",
                    type(node).__name__,
                    node.value if type(node).__name__ == "Name" else None,
                    str(parent_type) if parent_type else None,
                    str(_type) if _type else None,
                    str(input_type) if input_type else None,
                ]
            )

            # Make a query valid by adding missing selection sets.
            if (
                type(node).__name__ == "Field"
                and not node.selection_set
                and is_composite_type(get_named_type(_type))
            ):
                return Field(
                    alias=node.alias,
                    name=node.name,
                    arguments=node.arguments,
                    directives=node.directives,
                    selection_set=SelectionSet([Field(name=Name(value="__typename"))]),
                )

        def leave(
            self,
            node,  # type: Union[Argument, IntValue, Name]
            key,  # type: Union[int, str]
            parent,  # type: Union[List[Argument], Argument, Field]
            *args  # type: List[Any]
        ):
            # type: (...) -> None
            parent_type = type_info.get_parent_type()
            _type = type_info.get_type()
            input_type = type_info.get_input_type()
            visited.append(
                [
                    "leave",
                    type(node).__name__,
                    node.value if type(node).__name__ == "Name" else None,
                    str(parent_type) if parent_type else None,
                    str(_type) if _type else None,
                    str(input_type) if input_type else None,
                ]
            )

    edited_ast = visit(ast, TypeInfoVisitor(type_info, TestVisitor()))

    # assert print_ast(ast) == print_ast(parse(
    #     '{ human(id: 4) { name, pets }, alien }'
    # ))
    assert print_ast(edited_ast) == print_ast(
        parse("{ human(id: 4) { name, pets { __typename } }, alien { __typename } }")
    )
    assert visited == [
        ["enter", "Document", None, None, None, None],
        ["enter", "OperationDefinition", None, None, "QueryRoot", None],
        ["enter", "SelectionSet", None, "QueryRoot", "QueryRoot", None],
        ["enter", "Field", None, "QueryRoot", "Human", None],
        ["enter", "Name", "human", "QueryRoot", "Human", None],
        ["leave", "Name", "human", "QueryRoot", "Human", None],
        ["enter", "Argument", None, "QueryRoot", "Human", "ID"],
        ["enter", "Name", "id", "QueryRoot", "Human", "ID"],
        ["leave", "Name", "id", "QueryRoot", "Human", "ID"],
        ["enter", "IntValue", None, "QueryRoot", "Human", "ID"],
        ["leave", "IntValue", None, "QueryRoot", "Human", "ID"],
        ["leave", "Argument", None, "QueryRoot", "Human", "ID"],
        ["enter", "SelectionSet", None, "Human", "Human", None],
        ["enter", "Field", None, "Human", "String", None],
        ["enter", "Name", "name", "Human", "String", None],
        ["leave", "Name", "name", "Human", "String", None],
        ["leave", "Field", None, "Human", "String", None],
        ["enter", "Field", None, "Human", "[Pet]", None],
        ["enter", "Name", "pets", "Human", "[Pet]", None],
        ["leave", "Name", "pets", "Human", "[Pet]", None],
        ["enter", "SelectionSet", None, "Pet", "[Pet]", None],
        ["enter", "Field", None, "Pet", "String!", None],
        ["enter", "Name", "__typename", "Pet", "String!", None],
        ["leave", "Name", "__typename", "Pet", "String!", None],
        ["leave", "Field", None, "Pet", "String!", None],
        ["leave", "SelectionSet", None, "Pet", "[Pet]", None],
        ["leave", "Field", None, "Human", "[Pet]", None],
        ["leave", "SelectionSet", None, "Human", "Human", None],
        ["leave", "Field", None, "QueryRoot", "Human", None],
        ["enter", "Field", None, "QueryRoot", "Alien", None],
        ["enter", "Name", "alien", "QueryRoot", "Alien", None],
        ["leave", "Name", "alien", "QueryRoot", "Alien", None],
        ["enter", "SelectionSet", None, "Alien", "Alien", None],
        ["enter", "Field", None, "Alien", "String!", None],
        ["enter", "Name", "__typename", "Alien", "String!", None],
        ["leave", "Name", "__typename", "Alien", "String!", None],
        ["leave", "Field", None, "Alien", "String!", None],
        ["leave", "SelectionSet", None, "Alien", "Alien", None],
        ["leave", "Field", None, "QueryRoot", "Alien", None],
        ["leave", "SelectionSet", None, "QueryRoot", "QueryRoot", None],
        ["leave", "OperationDefinition", None, None, "QueryRoot", None],
        ["leave", "Document", None, None, None, None],
    ]

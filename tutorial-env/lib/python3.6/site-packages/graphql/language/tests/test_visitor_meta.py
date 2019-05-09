from graphql.language import ast
from graphql.language.visitor import Visitor


def test_visitor_meta_creates_enter_and_leave_handlers():
    # type: () -> None
    class MyVisitor(Visitor):
        def enter_OperationDefinition(self):
            pass

        def leave_OperationDefinition(self):
            pass

    assert MyVisitor._get_enter_handler(ast.OperationDefinition)
    assert MyVisitor._get_leave_handler(ast.OperationDefinition)


def test_visitor_inherits_parent_definitions():
    # type: () -> None
    class MyVisitor(Visitor):
        def enter_OperationDefinition(self):
            pass

        def leave_OperationDefinition(self):
            pass

    assert MyVisitor._get_enter_handler(ast.OperationDefinition)
    assert MyVisitor._get_leave_handler(ast.OperationDefinition)

    class MyVisitorSubclassed(MyVisitor):
        def enter_FragmentDefinition(self):
            pass

        def leave_FragmentDefinition(self):
            pass

    assert MyVisitorSubclassed._get_enter_handler(ast.OperationDefinition)
    assert MyVisitorSubclassed._get_leave_handler(ast.OperationDefinition)
    assert MyVisitorSubclassed._get_enter_handler(ast.FragmentDefinition)
    assert MyVisitorSubclassed._get_leave_handler(ast.FragmentDefinition)

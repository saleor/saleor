from graphql import parse
from graphql.utils.get_operation_ast import get_operation_ast


def test_gets_an_operation_from_a_simple_document():
    doc = parse("{ field }")
    assert get_operation_ast(doc) == doc.definitions[0]


def test_gets_an_operation_from_a_document_with_named_mutation_operation():
    doc = parse("mutation Test { field }")
    assert get_operation_ast(doc) == doc.definitions[0]


def test_gets_an_operation_from_a_document_with_named_subscription_operation():
    doc = parse("subscription Test { field }")
    assert get_operation_ast(doc) == doc.definitions[0]


def test_does_not_get_missing_operation():
    doc = parse("{ field } mutation Test { field }")
    assert not get_operation_ast(doc)


def test_does_not_get_ambiguous_unnamed_operation():
    doc = parse("{ field } mutation TestM { field } subscription TestSub { field }")
    assert not get_operation_ast(doc)


def test_does_not_get_ambiguous_named_operation():
    doc = parse(
        "query TestQ { field } mutation TestM { field } subscription TestSub { field }"
    )
    assert not get_operation_ast(doc)


def test_does_not_get_misnamed_operation():
    doc = parse(
        "query TestQ { field } mutation TestM { field } subscription TestSub { field }"
    )
    assert not get_operation_ast(doc, "Unknown")


def test_gets_named_operation():
    doc = parse(
        "query TestQ { field } mutation TestM { field } subscription TestS { field }"
    )
    assert get_operation_ast(doc, "TestQ") == doc.definitions[0]
    assert get_operation_ast(doc, "TestM") == doc.definitions[1]
    assert get_operation_ast(doc, "TestS") == doc.definitions[2]


def test_does_not_get_fragment():
    doc = parse("fragment Foo on Type { field }")
    assert not get_operation_ast(doc)
    assert not get_operation_ast(doc, "Foo")


def test_does_not_get_fragment_with_same_name_query():
    doc = parse("fragment Foo on Type { field } query Foo { field }")
    assert get_operation_ast(doc) == doc.definitions[1]
    assert get_operation_ast(doc, "Foo") == doc.definitions[1]

from graphql.language import ast
from graphql.language.parser import Loc, parse
from graphql.utils.ast_to_dict import ast_to_dict


def test_converts_simple_ast_to_dict():
    node = ast.Name(value="test", loc=Loc(start=5, end=10))

    assert ast_to_dict(node) == {"kind": "Name", "value": "test"}
    assert ast_to_dict(node, include_loc=True) == {
        "kind": "Name",
        "value": "test",
        "loc": {"start": 5, "end": 10},
    }


def test_converts_nested_ast_to_dict():
    parsed_ast = parse(
        """
        query x {
            someQuery(arg: "x") {
                a
                b
            }
            fragment Test on TestFoo {
                c
                d
            }
        }
    """
    )

    expected_ast_dict = {
        "definitions": [
            {
                "directives": [],
                "kind": "OperationDefinition",
                "name": {"kind": "Name", "value": "x"},
                "operation": "query",
                "selection_set": {
                    "kind": "SelectionSet",
                    "selections": [
                        {
                            "alias": None,
                            "arguments": [
                                {
                                    "kind": "Argument",
                                    "name": {"kind": "Name", "value": "arg"},
                                    "value": {"kind": "StringValue", "value": "x"},
                                }
                            ],
                            "directives": [],
                            "kind": "Field",
                            "name": {"kind": "Name", "value": "someQuery"},
                            "selection_set": {
                                "kind": "SelectionSet",
                                "selections": [
                                    {
                                        "alias": None,
                                        "arguments": [],
                                        "directives": [],
                                        "kind": "Field",
                                        "name": {"kind": "Name", "value": "a"},
                                        "selection_set": None,
                                    },
                                    {
                                        "alias": None,
                                        "arguments": [],
                                        "directives": [],
                                        "kind": "Field",
                                        "name": {"kind": "Name", "value": "b"},
                                        "selection_set": None,
                                    },
                                ],
                            },
                        },
                        {
                            "alias": None,
                            "arguments": [],
                            "directives": [],
                            "kind": "Field",
                            "name": {"kind": "Name", "value": "fragment"},
                            "selection_set": None,
                        },
                        {
                            "alias": None,
                            "arguments": [],
                            "directives": [],
                            "kind": "Field",
                            "name": {"kind": "Name", "value": "Test"},
                            "selection_set": None,
                        },
                        {
                            "alias": None,
                            "arguments": [],
                            "directives": [],
                            "kind": "Field",
                            "name": {"kind": "Name", "value": "on"},
                            "selection_set": None,
                        },
                        {
                            "alias": None,
                            "arguments": [],
                            "directives": [],
                            "kind": "Field",
                            "name": {"kind": "Name", "value": "TestFoo"},
                            "selection_set": {
                                "kind": "SelectionSet",
                                "selections": [
                                    {
                                        "alias": None,
                                        "arguments": [],
                                        "directives": [],
                                        "kind": "Field",
                                        "name": {"kind": "Name", "value": "c"},
                                        "selection_set": None,
                                    },
                                    {
                                        "alias": None,
                                        "arguments": [],
                                        "directives": [],
                                        "kind": "Field",
                                        "name": {"kind": "Name", "value": "d"},
                                        "selection_set": None,
                                    },
                                ],
                            },
                        },
                    ],
                },
                "variable_definitions": [],
            }
        ],
        "kind": "Document",
    }

    assert ast_to_dict(parsed_ast) == expected_ast_dict

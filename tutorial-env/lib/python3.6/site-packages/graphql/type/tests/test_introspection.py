import json
from collections import OrderedDict

from graphql import graphql
from graphql.error import format_error
from graphql.execution import execute
from graphql.language.parser import parse
from graphql.type import (
    GraphQLArgument,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLInputObjectField,
    GraphQLInputObjectType,
    GraphQLList,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
)
from graphql.utils.introspection_query import introspection_query
from graphql.validation.rules import ProvidedNonNullArguments

from ...pyutils.contain_subset import contain_subset


def test_executes_an_introspection_query():
    EmptySchema = GraphQLSchema(
        GraphQLObjectType("QueryRoot", {"f": GraphQLField(GraphQLString)})
    )

    result = graphql(EmptySchema, introspection_query)
    assert not result.errors
    expected = {
        "__schema": {
            "mutationType": None,
            "subscriptionType": None,
            "queryType": {"name": "QueryRoot"},
            "types": [
                {
                    "kind": "OBJECT",
                    "name": "QueryRoot",
                    "inputFields": None,
                    "interfaces": [],
                    "enumValues": None,
                    "possibleTypes": None,
                },
                {
                    "kind": "OBJECT",
                    "name": "__Schema",
                    "fields": [
                        {
                            "name": "types",
                            "args": [],
                            "type": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "LIST",
                                    "name": None,
                                    "ofType": {
                                        "kind": "NON_NULL",
                                        "name": None,
                                        "ofType": {"kind": "OBJECT", "name": "__Type"},
                                    },
                                },
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "queryType",
                            "args": [],
                            "type": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "OBJECT",
                                    "name": "__Type",
                                    "ofType": None,
                                },
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "mutationType",
                            "args": [],
                            "type": {
                                "kind": "OBJECT",
                                "name": "__Type",
                                "ofType": None,
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "subscriptionType",
                            "args": [],
                            "type": {
                                "kind": "OBJECT",
                                "name": "__Type",
                                "ofType": None,
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "directives",
                            "args": [],
                            "type": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "LIST",
                                    "name": None,
                                    "ofType": {
                                        "kind": "NON_NULL",
                                        "name": None,
                                        "ofType": {
                                            "kind": "OBJECT",
                                            "name": "__Directive",
                                        },
                                    },
                                },
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                    ],
                    "inputFields": None,
                    "interfaces": [],
                    "enumValues": None,
                    "possibleTypes": None,
                },
                {
                    "kind": "OBJECT",
                    "name": "__Type",
                    "fields": [
                        {
                            "name": "kind",
                            "args": [],
                            "type": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "ENUM",
                                    "name": "__TypeKind",
                                    "ofType": None,
                                },
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "name",
                            "args": [],
                            "type": {
                                "kind": "SCALAR",
                                "name": "String",
                                "ofType": None,
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "description",
                            "args": [],
                            "type": {
                                "kind": "SCALAR",
                                "name": "String",
                                "ofType": None,
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "fields",
                            "args": [
                                {
                                    "name": "includeDeprecated",
                                    "type": {
                                        "kind": "SCALAR",
                                        "name": "Boolean",
                                        "ofType": None,
                                    },
                                    "defaultValue": "false",
                                }
                            ],
                            "type": {
                                "kind": "LIST",
                                "name": None,
                                "ofType": {
                                    "kind": "NON_NULL",
                                    "name": None,
                                    "ofType": {
                                        "kind": "OBJECT",
                                        "name": "__Field",
                                        "ofType": None,
                                    },
                                },
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "interfaces",
                            "args": [],
                            "type": {
                                "kind": "LIST",
                                "name": None,
                                "ofType": {
                                    "kind": "NON_NULL",
                                    "name": None,
                                    "ofType": {
                                        "kind": "OBJECT",
                                        "name": "__Type",
                                        "ofType": None,
                                    },
                                },
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "possibleTypes",
                            "args": [],
                            "type": {
                                "kind": "LIST",
                                "name": None,
                                "ofType": {
                                    "kind": "NON_NULL",
                                    "name": None,
                                    "ofType": {
                                        "kind": "OBJECT",
                                        "name": "__Type",
                                        "ofType": None,
                                    },
                                },
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "enumValues",
                            "args": [
                                {
                                    "name": "includeDeprecated",
                                    "type": {
                                        "kind": "SCALAR",
                                        "name": "Boolean",
                                        "ofType": None,
                                    },
                                    "defaultValue": "false",
                                }
                            ],
                            "type": {
                                "kind": "LIST",
                                "name": None,
                                "ofType": {
                                    "kind": "NON_NULL",
                                    "name": None,
                                    "ofType": {
                                        "kind": "OBJECT",
                                        "name": "__EnumValue",
                                        "ofType": None,
                                    },
                                },
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "inputFields",
                            "args": [],
                            "type": {
                                "kind": "LIST",
                                "name": None,
                                "ofType": {
                                    "kind": "NON_NULL",
                                    "name": None,
                                    "ofType": {
                                        "kind": "OBJECT",
                                        "name": "__InputValue",
                                        "ofType": None,
                                    },
                                },
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "ofType",
                            "args": [],
                            "type": {
                                "kind": "OBJECT",
                                "name": "__Type",
                                "ofType": None,
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                    ],
                    "inputFields": None,
                    "interfaces": [],
                    "enumValues": None,
                    "possibleTypes": None,
                },
                {
                    "kind": "ENUM",
                    "name": "__TypeKind",
                    "fields": None,
                    "inputFields": None,
                    "interfaces": None,
                    "enumValues": [
                        {
                            "name": "SCALAR",
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "OBJECT",
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "INTERFACE",
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "UNION",
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "ENUM",
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "INPUT_OBJECT",
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "LIST",
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "NON_NULL",
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                    ],
                    "possibleTypes": None,
                },
                {
                    "kind": "SCALAR",
                    "name": "String",
                    "fields": None,
                    "inputFields": None,
                    "interfaces": None,
                    "enumValues": None,
                    "possibleTypes": None,
                },
                {
                    "kind": "SCALAR",
                    "name": "Boolean",
                    "fields": None,
                    "inputFields": None,
                    "interfaces": None,
                    "enumValues": None,
                    "possibleTypes": None,
                },
                {
                    "kind": "OBJECT",
                    "name": "__Field",
                    "fields": [
                        {
                            "name": "name",
                            "args": [],
                            "type": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "SCALAR",
                                    "name": "String",
                                    "ofType": None,
                                },
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "description",
                            "args": [],
                            "type": {
                                "kind": "SCALAR",
                                "name": "String",
                                "ofType": None,
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "args",
                            "args": [],
                            "type": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "LIST",
                                    "name": None,
                                    "ofType": {
                                        "kind": "NON_NULL",
                                        "name": None,
                                        "ofType": {
                                            "kind": "OBJECT",
                                            "name": "__InputValue",
                                        },
                                    },
                                },
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "type",
                            "args": [],
                            "type": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "OBJECT",
                                    "name": "__Type",
                                    "ofType": None,
                                },
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "isDeprecated",
                            "args": [],
                            "type": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "SCALAR",
                                    "name": "Boolean",
                                    "ofType": None,
                                },
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "deprecationReason",
                            "args": [],
                            "type": {
                                "kind": "SCALAR",
                                "name": "String",
                                "ofType": None,
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                    ],
                    "inputFields": None,
                    "interfaces": [],
                    "enumValues": None,
                    "possibleTypes": None,
                },
                {
                    "kind": "OBJECT",
                    "name": "__InputValue",
                    "fields": [
                        {
                            "name": "name",
                            "args": [],
                            "type": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "SCALAR",
                                    "name": "String",
                                    "ofType": None,
                                },
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "description",
                            "args": [],
                            "type": {
                                "kind": "SCALAR",
                                "name": "String",
                                "ofType": None,
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "type",
                            "args": [],
                            "type": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "OBJECT",
                                    "name": "__Type",
                                    "ofType": None,
                                },
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "defaultValue",
                            "args": [],
                            "type": {
                                "kind": "SCALAR",
                                "name": "String",
                                "ofType": None,
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                    ],
                    "inputFields": None,
                    "interfaces": [],
                    "enumValues": None,
                    "possibleTypes": None,
                },
                {
                    "kind": "OBJECT",
                    "name": "__EnumValue",
                    "fields": [
                        {
                            "name": "name",
                            "args": [],
                            "type": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "SCALAR",
                                    "name": "String",
                                    "ofType": None,
                                },
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "description",
                            "args": [],
                            "type": {
                                "kind": "SCALAR",
                                "name": "String",
                                "ofType": None,
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "isDeprecated",
                            "args": [],
                            "type": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "SCALAR",
                                    "name": "Boolean",
                                    "ofType": None,
                                },
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "deprecationReason",
                            "args": [],
                            "type": {
                                "kind": "SCALAR",
                                "name": "String",
                                "ofType": None,
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                    ],
                    "inputFields": None,
                    "interfaces": [],
                    "enumValues": None,
                    "possibleTypes": None,
                },
                {
                    "kind": "OBJECT",
                    "name": "__Directive",
                    "fields": [
                        {
                            "name": "name",
                            "args": [],
                            "type": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "SCALAR",
                                    "name": "String",
                                    "ofType": None,
                                },
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "description",
                            "args": [],
                            "type": {
                                "kind": "SCALAR",
                                "name": "String",
                                "ofType": None,
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "locations",
                            "args": [],
                            "type": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "LIST",
                                    "name": None,
                                    "ofType": {
                                        "kind": "NON_NULL",
                                        "name": None,
                                        "ofType": {
                                            "kind": "ENUM",
                                            "name": "__DirectiveLocation",
                                        },
                                    },
                                },
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "args",
                            "args": [],
                            "type": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "LIST",
                                    "name": None,
                                    "ofType": {
                                        "kind": "NON_NULL",
                                        "name": None,
                                        "ofType": {
                                            "kind": "OBJECT",
                                            "name": "__InputValue",
                                        },
                                    },
                                },
                            },
                            "isDeprecated": False,
                            "deprecationReason": None,
                        },
                        {
                            "name": "onOperation",
                            "args": [],
                            "type": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "SCALAR",
                                    "name": "Boolean",
                                    "ofType": None,
                                },
                            },
                            "isDeprecated": True,
                            "deprecationReason": "Use `locations`.",
                        },
                        {
                            "name": "onFragment",
                            "args": [],
                            "type": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "SCALAR",
                                    "name": "Boolean",
                                    "ofType": None,
                                },
                            },
                            "isDeprecated": True,
                            "deprecationReason": "Use `locations`.",
                        },
                        {
                            "name": "onField",
                            "args": [],
                            "type": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "SCALAR",
                                    "name": "Boolean",
                                    "ofType": None,
                                },
                            },
                            "isDeprecated": True,
                            "deprecationReason": "Use `locations`.",
                        },
                    ],
                    "inputFields": None,
                    "interfaces": [],
                    "enumValues": None,
                    "possibleTypes": None,
                },
                {
                    "kind": "ENUM",
                    "name": "__DirectiveLocation",
                    "fields": None,
                    "inputFields": None,
                    "interfaces": None,
                    "enumValues": [
                        {"name": "QUERY", "isDeprecated": False},
                        {"name": "MUTATION", "isDeprecated": False},
                        {"name": "SUBSCRIPTION", "isDeprecated": False},
                        {"name": "FIELD", "isDeprecated": False},
                        {"name": "FRAGMENT_DEFINITION", "isDeprecated": False},
                        {"name": "FRAGMENT_SPREAD", "isDeprecated": False},
                        {"name": "INLINE_FRAGMENT", "isDeprecated": False},
                    ],
                    "possibleTypes": None,
                },
            ],
            "directives": [
                {
                    "name": "include",
                    "locations": ["FIELD", "FRAGMENT_SPREAD", "INLINE_FRAGMENT"],
                    "args": [
                        {
                            "defaultValue": None,
                            "name": "if",
                            "type": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "SCALAR",
                                    "name": "Boolean",
                                    "ofType": None,
                                },
                            },
                        }
                    ],
                },
                {
                    "name": "skip",
                    "locations": ["FIELD", "FRAGMENT_SPREAD", "INLINE_FRAGMENT"],
                    "args": [
                        {
                            "defaultValue": None,
                            "name": "if",
                            "type": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "SCALAR",
                                    "name": "Boolean",
                                    "ofType": None,
                                },
                            },
                        }
                    ],
                },
            ],
        }
    }
    assert contain_subset(expected, result.data)


def test_introspects_on_input_object():
    TestInputObject = GraphQLInputObjectType(
        "TestInputObject",
        OrderedDict(
            [
                ("a", GraphQLInputObjectField(GraphQLString, default_value="foo")),
                ("b", GraphQLInputObjectField(GraphQLList(GraphQLString))),
            ]
        ),
    )
    TestType = GraphQLObjectType(
        "TestType",
        {
            "field": GraphQLField(
                type=GraphQLString,
                args={"complex": GraphQLArgument(TestInputObject)},
                resolver=lambda obj, info, **args: json.dumps(args.get("complex")),
            )
        },
    )
    schema = GraphQLSchema(TestType)
    request = """
      {
        __schema {
          types {
            kind
            name
            inputFields {
              name
              type { ...TypeRef }
              defaultValue
            }
          }
        }
      }
      fragment TypeRef on __Type {
        kind
        name
        ofType {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
            }
          }
        }
      }
    """
    result = graphql(schema, request)
    assert not result.errors
    assert {
        "kind": "INPUT_OBJECT",
        "name": "TestInputObject",
        "inputFields": [
            {
                "name": "a",
                "type": {"kind": "SCALAR", "name": "String", "ofType": None},
                "defaultValue": '"foo"',
            },
            {
                "name": "b",
                "type": {
                    "kind": "LIST",
                    "name": None,
                    "ofType": {"kind": "SCALAR", "name": "String", "ofType": None},
                },
                "defaultValue": None,
            },
        ],
    } in result.data["__schema"]["types"]


def test_supports_the_type_root_field():
    TestType = GraphQLObjectType("TestType", {"testField": GraphQLField(GraphQLString)})
    schema = GraphQLSchema(TestType)
    request = '{ __type(name: "TestType") { name } }'
    result = execute(schema, parse(request), object())
    assert not result.errors
    assert result.data == {"__type": {"name": "TestType"}}


def test_identifies_deprecated_fields():
    TestType = GraphQLObjectType(
        "TestType",
        OrderedDict(
            [
                ("nonDeprecated", GraphQLField(GraphQLString)),
                (
                    "deprecated",
                    GraphQLField(GraphQLString, deprecation_reason="Removed in 1.0"),
                ),
            ]
        ),
    )
    schema = GraphQLSchema(TestType)
    request = """{__type(name: "TestType") {
        name
        fields(includeDeprecated: true) {
            name
            isDeprecated
            deprecationReason
        }
    } }"""
    result = graphql(schema, request)
    assert not result.errors
    assert result.data == {
        "__type": {
            "name": "TestType",
            "fields": [
                {
                    "name": "nonDeprecated",
                    "isDeprecated": False,
                    "deprecationReason": None,
                },
                {
                    "name": "deprecated",
                    "isDeprecated": True,
                    "deprecationReason": "Removed in 1.0",
                },
            ],
        }
    }


def test_respects_the_includedeprecated_parameter_for_fields():
    TestType = GraphQLObjectType(
        "TestType",
        OrderedDict(
            [
                ("nonDeprecated", GraphQLField(GraphQLString)),
                (
                    "deprecated",
                    GraphQLField(GraphQLString, deprecation_reason="Removed in 1.0"),
                ),
            ]
        ),
    )
    schema = GraphQLSchema(TestType)
    request = """{__type(name: "TestType") {
        name
        trueFields: fields(includeDeprecated: true) { name }
        falseFields: fields(includeDeprecated: false) { name }
        omittedFields: fields { name }
    } }"""
    result = graphql(schema, request)
    assert not result.errors
    assert result.data == {
        "__type": {
            "name": "TestType",
            "trueFields": [{"name": "nonDeprecated"}, {"name": "deprecated"}],
            "falseFields": [{"name": "nonDeprecated"}],
            "omittedFields": [{"name": "nonDeprecated"}],
        }
    }


def test_identifies_deprecated_enum_values():
    TestEnum = GraphQLEnumType(
        "TestEnum",
        OrderedDict(
            [
                ("NONDEPRECATED", GraphQLEnumValue(0)),
                (
                    "DEPRECATED",
                    GraphQLEnumValue(1, deprecation_reason="Removed in 1.0"),
                ),
                ("ALSONONDEPRECATED", GraphQLEnumValue(2)),
            ]
        ),
    )
    TestType = GraphQLObjectType("TestType", {"testEnum": GraphQLField(TestEnum)})
    schema = GraphQLSchema(TestType)
    request = """{__type(name: "TestEnum") {
        name
        enumValues(includeDeprecated: true) {
            name
            isDeprecated
            deprecationReason
        }
    } }"""
    result = graphql(schema, request)
    assert not result.errors
    assert result.data == {
        "__type": {
            "name": "TestEnum",
            "enumValues": [
                {
                    "name": "NONDEPRECATED",
                    "isDeprecated": False,
                    "deprecationReason": None,
                },
                {
                    "name": "DEPRECATED",
                    "isDeprecated": True,
                    "deprecationReason": "Removed in 1.0",
                },
                {
                    "name": "ALSONONDEPRECATED",
                    "isDeprecated": False,
                    "deprecationReason": None,
                },
            ],
        }
    }


def test_respects_the_includedeprecated_parameter_for_enum_values():
    TestEnum = GraphQLEnumType(
        "TestEnum",
        OrderedDict(
            [
                ("NONDEPRECATED", GraphQLEnumValue(0)),
                (
                    "DEPRECATED",
                    GraphQLEnumValue(1, deprecation_reason="Removed in 1.0"),
                ),
                ("ALSONONDEPRECATED", GraphQLEnumValue(2)),
            ]
        ),
    )
    TestType = GraphQLObjectType("TestType", {"testEnum": GraphQLField(TestEnum)})
    schema = GraphQLSchema(TestType)
    request = """{__type(name: "TestEnum") {
        name
        trueValues: enumValues(includeDeprecated: true) { name }
        falseValues: enumValues(includeDeprecated: false) { name }
        omittedValues: enumValues { name }
    } }"""
    result = graphql(schema, request)
    assert not result.errors
    assert result.data == {
        "__type": {
            "name": "TestEnum",
            "trueValues": [
                {"name": "NONDEPRECATED"},
                {"name": "DEPRECATED"},
                {"name": "ALSONONDEPRECATED"},
            ],
            "falseValues": [{"name": "NONDEPRECATED"}, {"name": "ALSONONDEPRECATED"}],
            "omittedValues": [{"name": "NONDEPRECATED"}, {"name": "ALSONONDEPRECATED"}],
        }
    }


def test_fails_as_expected_on_the_type_root_field_without_an_arg():
    TestType = GraphQLObjectType("TestType", {"testField": GraphQLField(GraphQLString)})
    schema = GraphQLSchema(TestType)
    request = """
    {
        __type {
           name
        }
    }"""
    result = graphql(schema, request)
    expected_error = {
        "message": ProvidedNonNullArguments.missing_field_arg_message(
            "__type", "name", "String!"
        ),
        "locations": [dict(line=3, column=9)],
    }
    assert expected_error in [format_error(error) for error in result.errors]


def test_exposes_descriptions_on_types_and_fields():
    QueryRoot = GraphQLObjectType("QueryRoot", {"f": GraphQLField(GraphQLString)})
    schema = GraphQLSchema(QueryRoot)
    request = """{
      schemaType: __type(name: "__Schema") {
          name,
          description,
          fields {
            name,
            description
          }
        }
      }
    """
    result = graphql(schema, request)
    assert not result.errors
    assert result.data == {
        "schemaType": {
            "name": "__Schema",
            "description": "A GraphQL Schema defines the capabilities of a "
            + "GraphQL server. It exposes all available types and "
            + "directives on the server, as well as the entry "
            + "points for query, mutation and subscription operations.",
            "fields": [
                {
                    "name": "types",
                    "description": "A list of all types supported by this server.",
                },
                {
                    "name": "queryType",
                    "description": "The type that query operations will be rooted at.",
                },
                {
                    "name": "mutationType",
                    "description": "If this server supports mutation, the type that "
                    "mutation operations will be rooted at.",
                },
                {
                    "name": "subscriptionType",
                    "description": "If this server support subscription, the type "
                    "that subscription operations will be rooted at.",
                },
                {
                    "name": "directives",
                    "description": "A list of all directives supported by this server.",
                },
            ],
        }
    }


def test_exposes_descriptions_on_enums():
    QueryRoot = GraphQLObjectType("QueryRoot", {"f": GraphQLField(GraphQLString)})
    schema = GraphQLSchema(QueryRoot)
    request = """{
      typeKindType: __type(name: "__TypeKind") {
          name,
          description,
          enumValues {
            name,
            description
          }
        }
      }
    """
    result = graphql(schema, request)
    assert not result.errors
    assert result.data == {
        "typeKindType": {
            "name": "__TypeKind",
            "description": "An enum describing what kind of type a given `__Type` is",
            "enumValues": [
                {"description": "Indicates this type is a scalar.", "name": "SCALAR"},
                {
                    "description": "Indicates this type is an object. "
                    + "`fields` and `interfaces` are valid fields.",
                    "name": "OBJECT",
                },
                {
                    "description": "Indicates this type is an interface. "
                    + "`fields` and `possibleTypes` are valid fields.",
                    "name": "INTERFACE",
                },
                {
                    "description": "Indicates this type is a union. "
                    + "`possibleTypes` is a valid field.",
                    "name": "UNION",
                },
                {
                    "description": "Indicates this type is an enum. "
                    + "`enumValues` is a valid field.",
                    "name": "ENUM",
                },
                {
                    "description": "Indicates this type is an input object. "
                    + "`inputFields` is a valid field.",
                    "name": "INPUT_OBJECT",
                },
                {
                    "description": "Indicates this type is a list. "
                    + "`ofType` is a valid field.",
                    "name": "LIST",
                },
                {
                    "description": "Indicates this type is a non-null. "
                    + "`ofType` is a valid field.",
                    "name": "NON_NULL",
                },
            ],
        }
    }

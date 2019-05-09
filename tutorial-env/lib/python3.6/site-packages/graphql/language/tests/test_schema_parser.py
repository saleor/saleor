from pytest import raises

from graphql import Source, parse
from graphql.error import GraphQLSyntaxError
from graphql.language import ast
from graphql.language.parser import Loc
from typing import Callable


def create_loc_fn(body):
    # type: (str) -> Callable
    source = Source(body)
    return lambda start, end: Loc(start, end, source)


def test_parses_simple_type():
    # type: () -> None
    body = """
type Hello {
  world: String
}"""

    doc = parse(body)
    loc = create_loc_fn(body)

    expected = ast.Document(
        definitions=[
            ast.ObjectTypeDefinition(
                name=ast.Name(value="Hello", loc=loc(6, 11)),
                interfaces=[],
                directives=[],
                fields=[
                    ast.FieldDefinition(
                        name=ast.Name(value="world", loc=loc(16, 21)),
                        arguments=[],
                        type=ast.NamedType(
                            name=ast.Name(value="String", loc=loc(23, 29)),
                            loc=loc(23, 29),
                        ),
                        directives=[],
                        loc=loc(16, 29),
                    )
                ],
                loc=loc(1, 31),
            )
        ],
        loc=loc(1, 31),
    )
    assert doc == expected


def test_parses_simple_extension():
    # type: () -> None
    body = """
extend type Hello {
  world: String
}"""
    doc = parse(body)
    loc = create_loc_fn(body)

    expected = ast.Document(
        definitions=[
            ast.TypeExtensionDefinition(
                definition=ast.ObjectTypeDefinition(
                    name=ast.Name(value="Hello", loc=loc(13, 18)),
                    interfaces=[],
                    directives=[],
                    fields=[
                        ast.FieldDefinition(
                            name=ast.Name(value="world", loc=loc(23, 28)),
                            arguments=[],
                            type=ast.NamedType(
                                name=ast.Name(value="String", loc=loc(30, 36)),
                                loc=loc(30, 36),
                            ),
                            directives=[],
                            loc=loc(23, 36),
                        )
                    ],
                    loc=loc(8, 38),
                ),
                loc=loc(1, 38),
            )
        ],
        loc=loc(1, 38),
    )

    assert doc == expected


def test_simple_non_null_type():
    # type: () -> None
    body = """
type Hello {
  world: String!
}"""

    doc = parse(body)
    loc = create_loc_fn(body)
    expected = ast.Document(
        definitions=[
            ast.ObjectTypeDefinition(
                name=ast.Name(value="Hello", loc=loc(6, 11)),
                interfaces=[],
                directives=[],
                fields=[
                    ast.FieldDefinition(
                        name=ast.Name(value="world", loc=loc(16, 21)),
                        arguments=[],
                        type=ast.NonNullType(
                            type=ast.NamedType(
                                name=ast.Name(value="String", loc=loc(23, 29)),
                                loc=loc(23, 29),
                            ),
                            loc=loc(23, 30),
                        ),
                        directives=[],
                        loc=loc(16, 30),
                    )
                ],
                loc=loc(1, 32),
            )
        ],
        loc=loc(1, 32),
    )
    assert doc == expected


def test_parses_simple_type_inheriting_interface():
    # type: () -> None
    body = "type Hello implements World { }"
    loc = create_loc_fn(body)
    doc = parse(body)
    expected = ast.Document(
        definitions=[
            ast.ObjectTypeDefinition(
                name=ast.Name(value="Hello", loc=loc(5, 10)),
                interfaces=[
                    ast.NamedType(
                        name=ast.Name(value="World", loc=loc(22, 27)), loc=loc(22, 27)
                    )
                ],
                directives=[],
                fields=[],
                loc=loc(0, 31),
            )
        ],
        loc=loc(0, 31),
    )

    assert doc == expected


def test_parses_simple_type_inheriting_multiple_interfaces():
    # type: () -> None
    body = "type Hello implements Wo, rld { }"
    loc = create_loc_fn(body)
    doc = parse(body)
    expected = ast.Document(
        definitions=[
            ast.ObjectTypeDefinition(
                name=ast.Name(value="Hello", loc=loc(5, 10)),
                interfaces=[
                    ast.NamedType(
                        name=ast.Name(value="Wo", loc=loc(22, 24)), loc=loc(22, 24)
                    ),
                    ast.NamedType(
                        name=ast.Name(value="rld", loc=loc(26, 29)), loc=loc(26, 29)
                    ),
                ],
                directives=[],
                fields=[],
                loc=loc(0, 33),
            )
        ],
        loc=loc(0, 33),
    )
    assert doc == expected


def test_parses_single_value_enum():
    # type: () -> None
    body = "enum Hello { WORLD }"
    loc = create_loc_fn(body)
    doc = parse(body)
    expected = ast.Document(
        definitions=[
            ast.EnumTypeDefinition(
                name=ast.Name(value="Hello", loc=loc(5, 10)),
                directives=[],
                values=[
                    ast.EnumValueDefinition(
                        name=ast.Name(value="WORLD", loc=loc(13, 18)),
                        directives=[],
                        loc=loc(13, 18),
                    )
                ],
                loc=loc(0, 20),
            )
        ],
        loc=loc(0, 20),
    )

    assert doc == expected


def test_parses_double_value_enum():
    # type: () -> None
    body = "enum Hello { WO, RLD }"
    loc = create_loc_fn(body)
    doc = parse(body)
    expected = ast.Document(
        definitions=[
            ast.EnumTypeDefinition(
                name=ast.Name(value="Hello", loc=loc(5, 10)),
                directives=[],
                values=[
                    ast.EnumValueDefinition(
                        name=ast.Name(value="WO", loc=loc(13, 15)),
                        directives=[],
                        loc=loc(13, 15),
                    ),
                    ast.EnumValueDefinition(
                        name=ast.Name(value="RLD", loc=loc(17, 20)),
                        directives=[],
                        loc=loc(17, 20),
                    ),
                ],
                loc=loc(0, 22),
            )
        ],
        loc=loc(0, 22),
    )

    assert doc == expected


def test_parses_simple_interface():
    # type: () -> None
    body = """
interface Hello {
  world: String
}
"""
    loc = create_loc_fn(body)
    doc = parse(body)
    expected = ast.Document(
        definitions=[
            ast.InterfaceTypeDefinition(
                name=ast.Name(value="Hello", loc=loc(11, 16)),
                directives=[],
                fields=[
                    ast.FieldDefinition(
                        name=ast.Name(value="world", loc=loc(21, 26)),
                        arguments=[],
                        type=ast.NamedType(
                            name=ast.Name(value="String", loc=loc(28, 34)),
                            loc=loc(28, 34),
                        ),
                        directives=[],
                        loc=loc(21, 34),
                    )
                ],
                loc=loc(1, 36),
            )
        ],
        loc=loc(1, 37),
    )

    assert doc == expected


def test_parses_simple_field_with_arg():
    # type: () -> None
    body = """
type Hello {
  world(flag: Boolean): String
}"""
    loc = create_loc_fn(body)
    doc = parse(body)
    expected = ast.Document(
        definitions=[
            ast.ObjectTypeDefinition(
                name=ast.Name(value="Hello", loc=loc(6, 11)),
                interfaces=[],
                directives=[],
                fields=[
                    ast.FieldDefinition(
                        name=ast.Name(value="world", loc=loc(16, 21)),
                        arguments=[
                            ast.InputValueDefinition(
                                name=ast.Name(value="flag", loc=loc(22, 26)),
                                type=ast.NamedType(
                                    name=ast.Name(value="Boolean", loc=loc(28, 35)),
                                    loc=loc(28, 35),
                                ),
                                default_value=None,
                                directives=[],
                                loc=loc(22, 35),
                            )
                        ],
                        type=ast.NamedType(
                            name=ast.Name(value="String", loc=loc(38, 44)),
                            loc=loc(38, 44),
                        ),
                        directives=[],
                        loc=loc(16, 44),
                    )
                ],
                loc=loc(1, 46),
            )
        ],
        loc=loc(1, 46),
    )

    assert doc == expected


def test_parses_simple_field_with_arg_with_default_value():
    # type: () -> None
    body = """
type Hello {
  world(flag: Boolean = true): String
}"""
    loc = create_loc_fn(body)
    doc = parse(body)
    expected = ast.Document(
        definitions=[
            ast.ObjectTypeDefinition(
                name=ast.Name(value="Hello", loc=loc(6, 11)),
                interfaces=[],
                directives=[],
                fields=[
                    ast.FieldDefinition(
                        name=ast.Name(value="world", loc=loc(16, 21)),
                        arguments=[
                            ast.InputValueDefinition(
                                name=ast.Name(value="flag", loc=loc(22, 26)),
                                type=ast.NamedType(
                                    name=ast.Name(value="Boolean", loc=loc(28, 35)),
                                    loc=loc(28, 35),
                                ),
                                default_value=ast.BooleanValue(
                                    value=True, loc=loc(38, 42)
                                ),
                                directives=[],
                                loc=loc(22, 42),
                            )
                        ],
                        type=ast.NamedType(
                            name=ast.Name(value="String", loc=loc(45, 51)),
                            loc=loc(45, 51),
                        ),
                        directives=[],
                        loc=loc(16, 51),
                    )
                ],
                loc=loc(1, 53),
            )
        ],
        loc=loc(1, 53),
    )

    assert doc == expected


def test_parses_simple_field_with_list_arg():
    # type: () -> None
    body = """
type Hello {
  world(things: [String]): String
}"""
    loc = create_loc_fn(body)
    doc = parse(body)
    expected = ast.Document(
        definitions=[
            ast.ObjectTypeDefinition(
                name=ast.Name(value="Hello", loc=loc(6, 11)),
                interfaces=[],
                directives=[],
                fields=[
                    ast.FieldDefinition(
                        name=ast.Name(value="world", loc=loc(16, 21)),
                        arguments=[
                            ast.InputValueDefinition(
                                name=ast.Name(value="things", loc=loc(22, 28)),
                                type=ast.ListType(
                                    type=ast.NamedType(
                                        name=ast.Name(value="String", loc=loc(31, 37)),
                                        loc=loc(31, 37),
                                    ),
                                    loc=loc(30, 38),
                                ),
                                default_value=None,
                                directives=[],
                                loc=loc(22, 38),
                            )
                        ],
                        type=ast.NamedType(
                            name=ast.Name(value="String", loc=loc(41, 47)),
                            loc=loc(41, 47),
                        ),
                        directives=[],
                        loc=loc(16, 47),
                    )
                ],
                loc=loc(1, 49),
            )
        ],
        loc=loc(1, 49),
    )
    assert doc == expected


def test_parses_simple_field_with_two_args():
    # type: () -> None
    body = """
type Hello {
  world(argOne: Boolean, argTwo: Int): String
}"""
    loc = create_loc_fn(body)
    doc = parse(body)
    expected = ast.Document(
        definitions=[
            ast.ObjectTypeDefinition(
                name=ast.Name(value="Hello", loc=loc(6, 11)),
                interfaces=[],
                directives=[],
                fields=[
                    ast.FieldDefinition(
                        name=ast.Name(value="world", loc=loc(16, 21)),
                        arguments=[
                            ast.InputValueDefinition(
                                name=ast.Name(value="argOne", loc=loc(22, 28)),
                                type=ast.NamedType(
                                    name=ast.Name(value="Boolean", loc=loc(30, 37)),
                                    loc=loc(30, 37),
                                ),
                                default_value=None,
                                directives=[],
                                loc=loc(22, 37),
                            ),
                            ast.InputValueDefinition(
                                name=ast.Name(value="argTwo", loc=loc(39, 45)),
                                type=ast.NamedType(
                                    name=ast.Name(value="Int", loc=loc(47, 50)),
                                    loc=loc(47, 50),
                                ),
                                default_value=None,
                                directives=[],
                                loc=loc(39, 50),
                            ),
                        ],
                        type=ast.NamedType(
                            name=ast.Name(value="String", loc=loc(53, 59)),
                            loc=loc(53, 59),
                        ),
                        directives=[],
                        loc=loc(16, 59),
                    )
                ],
                loc=loc(1, 61),
            )
        ],
        loc=loc(1, 61),
    )
    assert doc == expected


def test_parses_simple_union():
    # type: () -> None
    body = "union Hello = World"
    loc = create_loc_fn(body)
    doc = parse(body)
    expected = ast.Document(
        definitions=[
            ast.UnionTypeDefinition(
                name=ast.Name(value="Hello", loc=loc(6, 11)),
                directives=[],
                types=[
                    ast.NamedType(
                        name=ast.Name(value="World", loc=loc(14, 19)), loc=loc(14, 19)
                    )
                ],
                loc=loc(0, 19),
            )
        ],
        loc=loc(0, 19),
    )
    assert doc == expected


def test_parses_union_with_two_types():
    # type: () -> None
    body = "union Hello = Wo | Rld"
    loc = create_loc_fn(body)
    doc = parse(body)
    expected = ast.Document(
        definitions=[
            ast.UnionTypeDefinition(
                name=ast.Name(value="Hello", loc=loc(6, 11)),
                directives=[],
                types=[
                    ast.NamedType(
                        name=ast.Name(value="Wo", loc=loc(14, 16)), loc=loc(14, 16)
                    ),
                    ast.NamedType(
                        name=ast.Name(value="Rld", loc=loc(19, 22)), loc=loc(19, 22)
                    ),
                ],
                loc=loc(0, 22),
            )
        ],
        loc=loc(0, 22),
    )
    assert doc == expected


def test_parses_scalar():
    # type: () -> None
    body = "scalar Hello"
    loc = create_loc_fn(body)
    doc = parse(body)
    expected = ast.Document(
        definitions=[
            ast.ScalarTypeDefinition(
                name=ast.Name(value="Hello", loc=loc(7, 12)),
                directives=[],
                loc=loc(0, 12),
            )
        ],
        loc=loc(0, 12),
    )
    assert doc == expected


def test_parses_simple_input_object():
    # type: () -> None
    body = """
input Hello {
  world: String
}"""
    loc = create_loc_fn(body)
    doc = parse(body)
    expected = ast.Document(
        definitions=[
            ast.InputObjectTypeDefinition(
                name=ast.Name(value="Hello", loc=loc(7, 12)),
                directives=[],
                fields=[
                    ast.InputValueDefinition(
                        name=ast.Name(value="world", loc=loc(17, 22)),
                        type=ast.NamedType(
                            name=ast.Name(value="String", loc=loc(24, 30)),
                            loc=loc(24, 30),
                        ),
                        default_value=None,
                        directives=[],
                        loc=loc(17, 30),
                    )
                ],
                loc=loc(1, 32),
            )
        ],
        loc=loc(1, 32),
    )
    assert doc == expected


def test_parsing_simple_input_object_with_args_should_fail():
    # type: () -> None
    body = """
input Hello {
  world(foo: Int): String
}
"""
    with raises(GraphQLSyntaxError) as excinfo:
        parse(body)

    assert "Syntax Error GraphQL (3:8) Expected :, found (" in excinfo.value.message

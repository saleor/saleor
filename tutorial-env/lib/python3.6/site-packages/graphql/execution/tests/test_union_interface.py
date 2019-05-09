# type: ignore
from graphql.execution import execute
from graphql.language.parser import parse
from graphql.type import (
    GraphQLBoolean,
    GraphQLField,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
    GraphQLUnionType,
)

# from typing import List
# from graphql.execution.base import ResolveInfo
# from graphql.type.definition import GraphQLObjectType
# from typing import Union


class Dog(object):
    def __init__(self, name, barks):
        self.name = name
        self.barks = barks


class Cat(object):
    def __init__(self, name, meows):
        self.name = name
        self.meows = meows


class Person(object):
    def __init__(self, name, pets, friends):
        # type: (str, List, List[Person]) -> None
        self.name = name
        self.pets = pets
        self.friends = friends


NamedType = GraphQLInterfaceType("Named", {"name": GraphQLField(GraphQLString)})

DogType = GraphQLObjectType(
    name="Dog",
    interfaces=[NamedType],
    fields={"name": GraphQLField(GraphQLString), "barks": GraphQLField(GraphQLBoolean)},
    is_type_of=lambda value, info: isinstance(value, Dog),
)

CatType = GraphQLObjectType(
    name="Cat",
    interfaces=[NamedType],
    fields={"name": GraphQLField(GraphQLString), "meows": GraphQLField(GraphQLBoolean)},
    is_type_of=lambda value, info: isinstance(value, Cat),
)


def resolve_pet_type(value, info):
    # type: (Union[Cat, Dog], ResolveInfo) -> GraphQLObjectType
    if isinstance(value, Dog):
        return DogType
    if isinstance(value, Cat):
        return CatType


PetType = GraphQLUnionType("Pet", [DogType, CatType], resolve_type=resolve_pet_type)

PersonType = GraphQLObjectType(
    name="Person",
    interfaces=[NamedType],
    fields={
        "name": GraphQLField(GraphQLString),
        "pets": GraphQLField(GraphQLList(PetType)),
        "friends": GraphQLField(GraphQLList(NamedType)),
    },
    is_type_of=lambda value, info: isinstance(value, Person),
)

schema = GraphQLSchema(query=PersonType, types=[PetType])

garfield = Cat("Garfield", False)
odie = Dog("Odie", True)
liz = Person("Liz", [], [])
john = Person("John", [garfield, odie], [liz, odie])


# Execute: Union and intersection types


def test_can_introspect_on_union_and_intersection_types():
    # type: () -> None
    ast = parse(
        """
    {
        Named: __type(name: "Named") {
            kind
            name
            fields { name }
            interfaces { name }
            possibleTypes { name }
            enumValues { name }
            inputFields { name }
        }
        Pet: __type(name: "Pet") {
            kind
            name
            fields { name }
            interfaces { name }
            possibleTypes { name }
            enumValues { name }
            inputFields { name }
        }
    }"""
    )

    result = execute(schema, ast)
    assert not result.errors
    assert result.data == {
        "Named": {
            "enumValues": None,
            "name": "Named",
            "kind": "INTERFACE",
            "interfaces": None,
            "fields": [{"name": "name"}],
            "possibleTypes": [{"name": "Person"}, {"name": "Dog"}, {"name": "Cat"}],
            "inputFields": None,
        },
        "Pet": {
            "enumValues": None,
            "name": "Pet",
            "kind": "UNION",
            "interfaces": None,
            "fields": None,
            "possibleTypes": [{"name": "Dog"}, {"name": "Cat"}],
            "inputFields": None,
        },
    }


def test_executes_using_union_types():
    # type: () -> None
    # NOTE: This is an *invalid* query, but it should be an *executable* query.
    ast = parse(
        """
        {
            __typename
            name
            pets {
                __typename
                name
                barks
                meows
            }
        }
    """
    )
    result = execute(schema, ast, john)
    assert not result.errors
    assert result.data == {
        "__typename": "Person",
        "name": "John",
        "pets": [
            {"__typename": "Cat", "name": "Garfield", "meows": False},
            {"__typename": "Dog", "name": "Odie", "barks": True},
        ],
    }


def test_executes_union_types_with_inline_fragment():
    # type: () -> None
    # This is the valid version of the query in the above test.
    ast = parse(
        """
      {
        __typename
        name
        pets {
          __typename
          ... on Dog {
            name
            barks
          }
          ... on Cat {
            name
            meows
          }
        }
      }
    """
    )
    result = execute(schema, ast, john)
    assert not result.errors
    assert result.data == {
        "__typename": "Person",
        "name": "John",
        "pets": [
            {"__typename": "Cat", "name": "Garfield", "meows": False},
            {"__typename": "Dog", "name": "Odie", "barks": True},
        ],
    }


def test_executes_using_interface_types():
    # type: () -> None
    # NOTE: This is an *invalid* query, but it should be an *executable* query.
    ast = parse(
        """
      {
        __typename
        name
        friends {
          __typename
          name
          barks
          meows
        }
      }
    """
    )
    result = execute(schema, ast, john)
    assert not result.errors
    assert result.data == {
        "__typename": "Person",
        "name": "John",
        "friends": [
            {"__typename": "Person", "name": "Liz"},
            {"__typename": "Dog", "name": "Odie", "barks": True},
        ],
    }


def test_executes_interface_types_with_inline_fragment():
    # type: () -> None
    # This is the valid version of the query in the above test.
    ast = parse(
        """
      {
        __typename
        name
        friends {
          __typename
          name
          ... on Dog {
            barks
          }
          ... on Cat {
            meows
          }
        }
      }
    """
    )
    result = execute(schema, ast, john)
    assert not result.errors
    assert result.data == {
        "__typename": "Person",
        "name": "John",
        "friends": [
            {"__typename": "Person", "name": "Liz"},
            {"__typename": "Dog", "name": "Odie", "barks": True},
        ],
    }


def test_allows_fragment_conditions_to_be_abstract_types():
    # type: () -> None
    ast = parse(
        """
      {
        __typename
        name
        pets { ...PetFields }
        friends { ...FriendFields }
      }
      fragment PetFields on Pet {
        __typename
        ... on Dog {
          name
          barks
        }
        ... on Cat {
          name
          meows
        }
      }
      fragment FriendFields on Named {
        __typename
        name
        ... on Dog {
          barks
        }
        ... on Cat {
          meows
        }
      }
    """
    )
    result = execute(schema, ast, john)
    assert not result.errors
    assert result.data == {
        "__typename": "Person",
        "name": "John",
        "pets": [
            {"__typename": "Cat", "name": "Garfield", "meows": False},
            {"__typename": "Dog", "name": "Odie", "barks": True},
        ],
        "friends": [
            {"__typename": "Person", "name": "Liz"},
            {"__typename": "Dog", "name": "Odie", "barks": True},
        ],
    }


def test_only_include_fields_from_matching_fragment_condition():
    # type: () -> None
    ast = parse(
        """
      {
        pets { ...PetFields }
      }
      fragment PetFields on Pet {
        __typename
        ... on Dog {
          name
        }
      }
    """
    )
    result = execute(schema, ast, john)
    assert not result.errors
    assert result.data == {
        "pets": [{"__typename": "Cat"}, {"__typename": "Dog", "name": "Odie"}]
    }


def test_gets_execution_info_in_resolver():
    # type: () -> None
    class encountered:
        schema = None
        root_value = None
        context = None

    def resolve_type(obj, info):
        # type: (Person, ResolveInfo) -> GraphQLObjectType
        encountered.schema = info.schema
        encountered.root_value = info.root_value
        encountered.context = context
        return PersonType2

    NamedType2 = GraphQLInterfaceType(
        name="Named",
        fields={"name": GraphQLField(GraphQLString)},
        resolve_type=resolve_type,
    )

    PersonType2 = GraphQLObjectType(
        name="Person",
        interfaces=[NamedType2],
        fields={
            "name": GraphQLField(GraphQLString),
            "friends": GraphQLField(GraphQLList(NamedType2)),
        },
    )

    schema2 = GraphQLSchema(query=PersonType2)
    john2 = Person("John", [], [liz])
    context = {"hey"}
    ast = parse("""{ name, friends { name } }""")

    result = execute(schema2, ast, john2, context_value=context)
    assert not result.errors
    assert result.data == {"name": "John", "friends": [{"name": "Liz"}]}

    assert encountered.schema == schema2
    assert encountered.root_value == john2
    assert encountered.context == context

import pytest
from promise import Promise

from ...types import (
    ID,
    Argument,
    Field,
    InputField,
    InputObjectType,
    NonNull,
    ObjectType,
    Schema,
)
from ...types.scalars import String
from ..mutation import ClientIDMutation


class SharedFields(object):
    shared = String()


class MyNode(ObjectType):
    # class Meta:
    #     interfaces = (Node, )
    id = ID()
    name = String()


class SaySomething(ClientIDMutation):
    class Input:
        what = String()

    phrase = String()

    @staticmethod
    def mutate_and_get_payload(self, info, what, client_mutation_id=None):
        return SaySomething(phrase=str(what))


class FixedSaySomething(object):
    __slots__ = ("phrase",)

    def __init__(self, phrase):
        self.phrase = phrase


class SaySomethingFixed(ClientIDMutation):
    class Input:
        what = String()

    phrase = String()

    @staticmethod
    def mutate_and_get_payload(self, info, what, client_mutation_id=None):
        return FixedSaySomething(phrase=str(what))


class SaySomethingPromise(ClientIDMutation):
    class Input:
        what = String()

    phrase = String()

    @staticmethod
    def mutate_and_get_payload(self, info, what, client_mutation_id=None):
        return Promise.resolve(SaySomething(phrase=str(what)))


# MyEdge = MyNode.Connection.Edge
class MyEdge(ObjectType):
    node = Field(MyNode)
    cursor = String()


class OtherMutation(ClientIDMutation):
    class Input(SharedFields):
        additional_field = String()

    name = String()
    my_node_edge = Field(MyEdge)

    @staticmethod
    def mutate_and_get_payload(
        self, info, shared="", additional_field="", client_mutation_id=None
    ):
        edge_type = MyEdge
        return OtherMutation(
            name=shared + additional_field,
            my_node_edge=edge_type(cursor="1", node=MyNode(name="name")),
        )


class RootQuery(ObjectType):
    something = String()


class Mutation(ObjectType):
    say = SaySomething.Field()
    say_fixed = SaySomethingFixed.Field()
    say_promise = SaySomethingPromise.Field()
    other = OtherMutation.Field()


schema = Schema(query=RootQuery, mutation=Mutation)


def test_no_mutate_and_get_payload():
    with pytest.raises(AssertionError) as excinfo:

        class MyMutation(ClientIDMutation):
            pass

    assert (
        "MyMutation.mutate_and_get_payload method is required in a ClientIDMutation."
        == str(excinfo.value)
    )


def test_mutation():
    fields = SaySomething._meta.fields
    assert list(fields.keys()) == ["phrase", "client_mutation_id"]
    assert SaySomething._meta.name == "SaySomethingPayload"
    assert isinstance(fields["phrase"], Field)
    field = SaySomething.Field()
    assert field.type == SaySomething
    assert list(field.args.keys()) == ["input"]
    assert isinstance(field.args["input"], Argument)
    assert isinstance(field.args["input"].type, NonNull)
    assert field.args["input"].type.of_type == SaySomething.Input
    assert isinstance(fields["client_mutation_id"], Field)
    assert fields["client_mutation_id"].name == "clientMutationId"
    assert fields["client_mutation_id"].type == String


def test_mutation_input():
    Input = SaySomething.Input
    assert issubclass(Input, InputObjectType)
    fields = Input._meta.fields
    assert list(fields.keys()) == ["what", "client_mutation_id"]
    assert isinstance(fields["what"], InputField)
    assert fields["what"].type == String
    assert isinstance(fields["client_mutation_id"], InputField)
    assert fields["client_mutation_id"].type == String


def test_subclassed_mutation():
    fields = OtherMutation._meta.fields
    assert list(fields.keys()) == ["name", "my_node_edge", "client_mutation_id"]
    assert isinstance(fields["name"], Field)
    field = OtherMutation.Field()
    assert field.type == OtherMutation
    assert list(field.args.keys()) == ["input"]
    assert isinstance(field.args["input"], Argument)
    assert isinstance(field.args["input"].type, NonNull)
    assert field.args["input"].type.of_type == OtherMutation.Input


def test_subclassed_mutation_input():
    Input = OtherMutation.Input
    assert issubclass(Input, InputObjectType)
    fields = Input._meta.fields
    assert list(fields.keys()) == ["shared", "additional_field", "client_mutation_id"]
    assert isinstance(fields["shared"], InputField)
    assert fields["shared"].type == String
    assert isinstance(fields["additional_field"], InputField)
    assert fields["additional_field"].type == String
    assert isinstance(fields["client_mutation_id"], InputField)
    assert fields["client_mutation_id"].type == String


def test_node_query():
    executed = schema.execute(
        'mutation a { say(input: {what:"hello", clientMutationId:"1"}) { phrase } }'
    )
    assert not executed.errors
    assert executed.data == {"say": {"phrase": "hello"}}


def test_node_query_fixed():
    executed = schema.execute(
        'mutation a { sayFixed(input: {what:"hello", clientMutationId:"1"}) { phrase } }'
    )
    assert "Cannot set client_mutation_id in the payload object" in str(
        executed.errors[0]
    )


def test_node_query_promise():
    executed = schema.execute(
        'mutation a { sayPromise(input: {what:"hello", clientMutationId:"1"}) { phrase } }'
    )
    assert not executed.errors
    assert executed.data == {"sayPromise": {"phrase": "hello"}}


def test_edge_query():
    executed = schema.execute(
        'mutation a { other(input: {clientMutationId:"1"}) { clientMutationId, myNodeEdge { cursor node { name }} } }'
    )
    assert not executed.errors
    assert dict(executed.data) == {
        "other": {
            "clientMutationId": "1",
            "myNodeEdge": {"cursor": "1", "node": {"name": "name"}},
        }
    }

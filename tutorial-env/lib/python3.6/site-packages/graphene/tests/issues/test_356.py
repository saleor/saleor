# https://github.com/graphql-python/graphene/issues/356

import pytest

import graphene
from graphene import relay


class SomeTypeOne(graphene.ObjectType):
    pass


class SomeTypeTwo(graphene.ObjectType):
    pass


class MyUnion(graphene.Union):
    class Meta:
        types = (SomeTypeOne, SomeTypeTwo)


def test_issue():
    class Query(graphene.ObjectType):
        things = relay.ConnectionField(MyUnion)

    with pytest.raises(Exception) as exc_info:
        graphene.Schema(query=Query)

    assert str(exc_info.value) == (
        "IterableConnectionField type have to be a subclass of Connection. "
        'Received "MyUnion".'
    )

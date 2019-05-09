import datetime
import graphene
from graphene import relay
from graphene.types.resolver import dict_resolver

from ..deduplicator import deflate


def test_does_not_modify_object_without_typename_and_id():
    response = {"foo": "bar"}

    deflated_response = deflate(response)
    assert deflated_response == {"foo": "bar"}


def test_does_not_modify_first_instance_of_an_object():
    response = {
        "data": [
            {"__typename": "foo", "id": 1, "name": "foo"},
            {"__typename": "foo", "id": 1, "name": "foo"},
        ]
    }

    deflated_response = deflate(response)

    assert deflated_response == {
        "data": [
            {"__typename": "foo", "id": 1, "name": "foo"},
            {"__typename": "foo", "id": 1},
        ]
    }


def test_does_not_modify_first_instance_of_an_object_nested():
    response = {
        "data": [
            {
                "__typename": "foo",
                "bar1": {"__typename": "bar", "id": 1, "name": "bar"},
                "bar2": {"__typename": "bar", "id": 1, "name": "bar"},
                "id": 1,
            },
            {
                "__typename": "foo",
                "bar1": {"__typename": "bar", "id": 1, "name": "bar"},
                "bar2": {"__typename": "bar", "id": 1, "name": "bar"},
                "id": 2,
            },
        ]
    }

    deflated_response = deflate(response)

    assert deflated_response == {
        "data": [
            {
                "__typename": "foo",
                "bar1": {"__typename": "bar", "id": 1, "name": "bar"},
                "bar2": {"__typename": "bar", "id": 1, "name": "bar"},
                "id": 1,
            },
            {
                "__typename": "foo",
                "bar1": {"__typename": "bar", "id": 1},
                "bar2": {"__typename": "bar", "id": 1},
                "id": 2,
            },
        ]
    }


def test_does_not_modify_input():
    response = {
        "data": [
            {"__typename": "foo", "id": 1, "name": "foo"},
            {"__typename": "foo", "id": 1, "name": "foo"},
        ]
    }

    deflate(response)

    assert response == {
        "data": [
            {"__typename": "foo", "id": 1, "name": "foo"},
            {"__typename": "foo", "id": 1, "name": "foo"},
        ]
    }


TEST_DATA = {
    "events": [
        {"id": "568", "date": datetime.date(2017, 5, 19), "movie": "1198359"},
        {"id": "234", "date": datetime.date(2017, 5, 20), "movie": "1198359"},
    ],
    "movies": {
        "1198359": {
            "name": "King Arthur: Legend of the Sword",
            "synopsis": (
                "When the child Arthur's father is murdered, Vortigern, "
                "Arthur's uncle, seizes the crown. Robbed of his birthright and "
                "with no idea who he truly is..."
            ),
        }
    },
}


def test_example_end_to_end():
    class Movie(graphene.ObjectType):
        class Meta:
            interfaces = (relay.Node,)
            default_resolver = dict_resolver

        name = graphene.String(required=True)
        synopsis = graphene.String(required=True)

    class Event(graphene.ObjectType):
        class Meta:
            interfaces = (relay.Node,)
            default_resolver = dict_resolver

        movie = graphene.Field(Movie, required=True)
        date = graphene.types.datetime.Date(required=True)

        def resolve_movie(event, info):
            return TEST_DATA["movies"][event["movie"]]

    class Query(graphene.ObjectType):
        events = graphene.List(graphene.NonNull(Event), required=True)

        def resolve_events(_, info):
            return TEST_DATA["events"]

    schema = graphene.Schema(query=Query)
    query = """\
        {
            events {
                __typename
                id
                date
                movie {
                    __typename
                    id
                    name
                    synopsis
                }
            }
        }
    """
    result = schema.execute(query)
    assert not result.errors

    result.data = deflate(result.data)
    assert result.data == {
        "events": [
            {
                "__typename": "Event",
                "id": "RXZlbnQ6NTY4",
                "date": "2017-05-19",
                "movie": {
                    "__typename": "Movie",
                    "id": "TW92aWU6Tm9uZQ==",
                    "name": "King Arthur: Legend of the Sword",
                    "synopsis": (
                        "When the child Arthur's father is murdered, Vortigern, "
                        "Arthur's uncle, seizes the crown. Robbed of his birthright and "
                        "with no idea who he truly is..."
                    ),
                },
            },
            {
                "__typename": "Event",
                "id": "RXZlbnQ6MjM0",
                "date": "2017-05-20",
                "movie": {"__typename": "Movie", "id": "TW92aWU6Tm9uZQ=="},
            },
        ]
    }

import pytest

import graphene
from graphene.relay import Node
from graphene_django import DjangoConnectionField, DjangoObjectType

from ...tests.models import Reporter
from ..middleware import DjangoDebugMiddleware
from ..types import DjangoDebug


class context(object):
    pass


# from examples.starwars_django.models import Character

pytestmark = pytest.mark.django_db


def test_should_query_field():
    r1 = Reporter(last_name="ABA")
    r1.save()
    r2 = Reporter(last_name="Griffin")
    r2.save()

    class ReporterType(DjangoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)

    class Query(graphene.ObjectType):
        reporter = graphene.Field(ReporterType)
        debug = graphene.Field(DjangoDebug, name="__debug")

        def resolve_reporter(self, info, **args):
            return Reporter.objects.first()

    query = """
        query ReporterQuery {
          reporter {
            lastName
          }
          __debug {
            sql {
              rawSql
            }
          }
        }
    """
    expected = {
        "reporter": {"lastName": "ABA"},
        "__debug": {
            "sql": [{"rawSql": str(Reporter.objects.order_by("pk")[:1].query)}]
        },
    }
    schema = graphene.Schema(query=Query)
    result = schema.execute(
        query, context_value=context(), middleware=[DjangoDebugMiddleware()]
    )
    assert not result.errors
    assert result.data == expected


def test_should_query_list():
    r1 = Reporter(last_name="ABA")
    r1.save()
    r2 = Reporter(last_name="Griffin")
    r2.save()

    class ReporterType(DjangoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)

    class Query(graphene.ObjectType):
        all_reporters = graphene.List(ReporterType)
        debug = graphene.Field(DjangoDebug, name="__debug")

        def resolve_all_reporters(self, info, **args):
            return Reporter.objects.all()

    query = """
        query ReporterQuery {
          allReporters {
            lastName
          }
          __debug {
            sql {
              rawSql
            }
          }
        }
    """
    expected = {
        "allReporters": [{"lastName": "ABA"}, {"lastName": "Griffin"}],
        "__debug": {"sql": [{"rawSql": str(Reporter.objects.all().query)}]},
    }
    schema = graphene.Schema(query=Query)
    result = schema.execute(
        query, context_value=context(), middleware=[DjangoDebugMiddleware()]
    )
    assert not result.errors
    assert result.data == expected


def test_should_query_connection():
    r1 = Reporter(last_name="ABA")
    r1.save()
    r2 = Reporter(last_name="Griffin")
    r2.save()

    class ReporterType(DjangoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)

    class Query(graphene.ObjectType):
        all_reporters = DjangoConnectionField(ReporterType)
        debug = graphene.Field(DjangoDebug, name="__debug")

        def resolve_all_reporters(self, info, **args):
            return Reporter.objects.all()

    query = """
        query ReporterQuery {
          allReporters(first:1) {
            edges {
              node {
                lastName
              }
            }
          }
          __debug {
            sql {
              rawSql
            }
          }
        }
    """
    expected = {"allReporters": {"edges": [{"node": {"lastName": "ABA"}}]}}
    schema = graphene.Schema(query=Query)
    result = schema.execute(
        query, context_value=context(), middleware=[DjangoDebugMiddleware()]
    )
    assert not result.errors
    assert result.data["allReporters"] == expected["allReporters"]
    assert "COUNT" in result.data["__debug"]["sql"][0]["rawSql"]
    query = str(Reporter.objects.all()[:1].query)
    assert result.data["__debug"]["sql"][1]["rawSql"] == query


def test_should_query_connectionfilter():
    from ...filter import DjangoFilterConnectionField

    r1 = Reporter(last_name="ABA")
    r1.save()
    r2 = Reporter(last_name="Griffin")
    r2.save()

    class ReporterType(DjangoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)

    class Query(graphene.ObjectType):
        all_reporters = DjangoFilterConnectionField(ReporterType, fields=["last_name"])
        s = graphene.String(resolver=lambda *_: "S")
        debug = graphene.Field(DjangoDebug, name="__debug")

        def resolve_all_reporters(self, info, **args):
            return Reporter.objects.all()

    query = """
        query ReporterQuery {
          allReporters(first:1) {
            edges {
              node {
                lastName
              }
            }
          }
          __debug {
            sql {
              rawSql
            }
          }
        }
    """
    expected = {"allReporters": {"edges": [{"node": {"lastName": "ABA"}}]}}
    schema = graphene.Schema(query=Query)
    result = schema.execute(
        query, context_value=context(), middleware=[DjangoDebugMiddleware()]
    )
    assert not result.errors
    assert result.data["allReporters"] == expected["allReporters"]
    assert "COUNT" in result.data["__debug"]["sql"][0]["rawSql"]
    query = str(Reporter.objects.all()[:1].query)
    assert result.data["__debug"]["sql"][1]["rawSql"] == query

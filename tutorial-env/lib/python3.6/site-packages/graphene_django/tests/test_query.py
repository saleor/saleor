import datetime

import pytest
from django.db import models
from django.utils.functional import SimpleLazyObject
from py.test import raises

from django.db.models import Q

import graphene
from graphene.relay import Node

from ..utils import DJANGO_FILTER_INSTALLED
from ..compat import MissingType, JSONField
from ..fields import DjangoConnectionField
from ..types import DjangoObjectType
from ..settings import graphene_settings
from .models import Article, CNNReporter, Reporter, Film, FilmDetails

pytestmark = pytest.mark.django_db


def test_should_query_only_fields():
    with raises(Exception):

        class ReporterType(DjangoObjectType):
            class Meta:
                model = Reporter
                only_fields = ("articles",)

        schema = graphene.Schema(query=ReporterType)
        query = """
            query ReporterQuery {
              articles
            }
        """
        result = schema.execute(query)
        assert not result.errors


def test_should_query_simplelazy_objects():
    class ReporterType(DjangoObjectType):
        class Meta:
            model = Reporter
            only_fields = ("id",)

    class Query(graphene.ObjectType):
        reporter = graphene.Field(ReporterType)

        def resolve_reporter(self, info):
            return SimpleLazyObject(lambda: Reporter(id=1))

    schema = graphene.Schema(query=Query)
    query = """
        query {
          reporter {
            id
          }
        }
    """
    result = schema.execute(query)
    assert not result.errors
    assert result.data == {"reporter": {"id": "1"}}


def test_should_query_well():
    class ReporterType(DjangoObjectType):
        class Meta:
            model = Reporter

    class Query(graphene.ObjectType):
        reporter = graphene.Field(ReporterType)

        def resolve_reporter(self, info):
            return Reporter(first_name="ABA", last_name="X")

    query = """
        query ReporterQuery {
          reporter {
            firstName,
            lastName,
            email
          }
        }
    """
    expected = {"reporter": {"firstName": "ABA", "lastName": "X", "email": ""}}
    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert result.data == expected


@pytest.mark.skipif(JSONField is MissingType, reason="RangeField should exist")
def test_should_query_postgres_fields():
    from django.contrib.postgres.fields import (
        IntegerRangeField,
        ArrayField,
        JSONField,
        HStoreField,
    )

    class Event(models.Model):
        ages = IntegerRangeField(help_text="The age ranges")
        data = JSONField(help_text="Data")
        store = HStoreField()
        tags = ArrayField(models.CharField(max_length=50))

    class EventType(DjangoObjectType):
        class Meta:
            model = Event

    class Query(graphene.ObjectType):
        event = graphene.Field(EventType)

        def resolve_event(self, info):
            return Event(
                ages=(0, 10),
                data={"angry_babies": True},
                store={"h": "store"},
                tags=["child", "angry", "babies"],
            )

    schema = graphene.Schema(query=Query)
    query = """
        query myQuery {
          event {
            ages
            tags
            data
            store
          }
        }
    """
    expected = {
        "event": {
            "ages": [0, 10],
            "tags": ["child", "angry", "babies"],
            "data": '{"angry_babies": true}',
            "store": '{"h": "store"}',
        }
    }
    result = schema.execute(query)
    assert not result.errors
    assert result.data == expected


def test_should_node():
    # reset_global_registry()
    # Node._meta.registry = get_global_registry()

    class ReporterNode(DjangoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)

        @classmethod
        def get_node(cls, info, id):
            return Reporter(id=2, first_name="Cookie Monster")

        def resolve_articles(self, info, **args):
            return [Article(headline="Hi!")]

    class ArticleNode(DjangoObjectType):
        class Meta:
            model = Article
            interfaces = (Node,)

        @classmethod
        def get_node(cls, info, id):
            return Article(
                id=1, headline="Article node", pub_date=datetime.date(2002, 3, 11)
            )

    class Query(graphene.ObjectType):
        node = Node.Field()
        reporter = graphene.Field(ReporterNode)
        article = graphene.Field(ArticleNode)

        def resolve_reporter(self, info):
            return Reporter(id=1, first_name="ABA", last_name="X")

    query = """
        query ReporterQuery {
          reporter {
            id,
            firstName,
            articles {
              edges {
                node {
                  headline
                }
              }
            }
            lastName,
            email
          }
          myArticle: node(id:"QXJ0aWNsZU5vZGU6MQ==") {
            id
            ... on ReporterNode {
                firstName
            }
            ... on ArticleNode {
                headline
                pubDate
            }
          }
        }
    """
    expected = {
        "reporter": {
            "id": "UmVwb3J0ZXJOb2RlOjE=",
            "firstName": "ABA",
            "lastName": "X",
            "email": "",
            "articles": {"edges": [{"node": {"headline": "Hi!"}}]},
        },
        "myArticle": {
            "id": "QXJ0aWNsZU5vZGU6MQ==",
            "headline": "Article node",
            "pubDate": "2002-03-11",
        },
    }
    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert result.data == expected


def test_should_query_connectionfields():
    class ReporterType(DjangoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)
            only_fields = ("articles",)

    class Query(graphene.ObjectType):
        all_reporters = DjangoConnectionField(ReporterType)

        def resolve_all_reporters(self, info, **args):
            return [Reporter(id=1)]

    schema = graphene.Schema(query=Query)
    query = """
        query ReporterConnectionQuery {
          allReporters {
            pageInfo {
              hasNextPage
            }
            edges {
              node {
                id
              }
            }
          }
        }
    """
    result = schema.execute(query)
    assert not result.errors
    assert result.data == {
        "allReporters": {
            "pageInfo": {"hasNextPage": False},
            "edges": [{"node": {"id": "UmVwb3J0ZXJUeXBlOjE="}}],
        }
    }


def test_should_keep_annotations():
    from django.db.models import Count, Avg

    class ReporterType(DjangoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)
            only_fields = ("articles",)

    class ArticleType(DjangoObjectType):
        class Meta:
            model = Article
            interfaces = (Node,)
            filter_fields = ("lang",)

    class Query(graphene.ObjectType):
        all_reporters = DjangoConnectionField(ReporterType)
        all_articles = DjangoConnectionField(ArticleType)

        def resolve_all_reporters(self, info, **args):
            return Reporter.objects.annotate(articles_c=Count("articles")).order_by(
                "articles_c"
            )

        def resolve_all_articles(self, info, **args):
            return Article.objects.annotate(import_avg=Avg("importance")).order_by(
                "import_avg"
            )

    schema = graphene.Schema(query=Query)
    query = """
        query ReporterConnectionQuery {
          allReporters {
            pageInfo {
              hasNextPage
            }
            edges {
              node {
                id
              }
            }
          }
          allArticles {
            pageInfo {
              hasNextPage
            }
            edges {
              node {
                id
              }
            }
          }
        }
    """
    result = schema.execute(query)
    assert not result.errors


@pytest.mark.skipif(
    not DJANGO_FILTER_INSTALLED, reason="django-filter should be installed"
)
def test_should_query_node_filtering():
    class ReporterType(DjangoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)

    class ArticleType(DjangoObjectType):
        class Meta:
            model = Article
            interfaces = (Node,)
            filter_fields = ("lang",)

    class Query(graphene.ObjectType):
        all_reporters = DjangoConnectionField(ReporterType)

    r = Reporter.objects.create(
        first_name="John", last_name="Doe", email="johndoe@example.com", a_choice=1
    )
    Article.objects.create(
        headline="Article Node 1",
        pub_date=datetime.date.today(),
        pub_date_time=datetime.datetime.now(),
        reporter=r,
        editor=r,
        lang="es",
    )
    Article.objects.create(
        headline="Article Node 2",
        pub_date=datetime.date.today(),
        pub_date_time=datetime.datetime.now(),
        reporter=r,
        editor=r,
        lang="en",
    )

    schema = graphene.Schema(query=Query)
    query = """
        query NodeFilteringQuery {
            allReporters {
                edges {
                    node {
                        id
                        articles(lang: "es") {
                            edges {
                                node {
                                    id
                                }
                            }
                        }
                    }
                }
            }
        }
    """

    expected = {
        "allReporters": {
            "edges": [
                {
                    "node": {
                        "id": "UmVwb3J0ZXJUeXBlOjE=",
                        "articles": {
                            "edges": [{"node": {"id": "QXJ0aWNsZVR5cGU6MQ=="}}]
                        },
                    }
                }
            ]
        }
    }

    result = schema.execute(query)
    assert not result.errors
    assert result.data == expected


@pytest.mark.skipif(
    not DJANGO_FILTER_INSTALLED, reason="django-filter should be installed"
)
def test_should_query_node_filtering_with_distinct_queryset():
    class FilmType(DjangoObjectType):
        class Meta:
            model = Film
            interfaces = (Node,)
            filter_fields = ("genre",)

    class Query(graphene.ObjectType):
        films = DjangoConnectionField(FilmType)

        # def resolve_all_reporters_with_berlin_films(self, args, context, info):
        #    return Reporter.objects.filter(Q(films__film__location__contains="Berlin") | Q(a_choice=1))

        def resolve_films(self, info, **args):
            return Film.objects.filter(
                Q(details__location__contains="Berlin") | Q(genre__in=["ot"])
            ).distinct()

    f = Film.objects.create()
    fd = FilmDetails.objects.create(location="Berlin", film=f)

    schema = graphene.Schema(query=Query)
    query = """
        query NodeFilteringQuery {
            films {
                edges {
                    node {
                        genre
                    }
                }
            }
        }
    """

    expected = {"films": {"edges": [{"node": {"genre": "OT"}}]}}

    result = schema.execute(query)
    assert not result.errors
    assert result.data == expected


@pytest.mark.skipif(
    not DJANGO_FILTER_INSTALLED, reason="django-filter should be installed"
)
def test_should_query_node_multiple_filtering():
    class ReporterType(DjangoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)

    class ArticleType(DjangoObjectType):
        class Meta:
            model = Article
            interfaces = (Node,)
            filter_fields = ("lang", "headline")

    class Query(graphene.ObjectType):
        all_reporters = DjangoConnectionField(ReporterType)

    r = Reporter.objects.create(
        first_name="John", last_name="Doe", email="johndoe@example.com", a_choice=1
    )
    Article.objects.create(
        headline="Article Node 1",
        pub_date=datetime.date.today(),
        pub_date_time=datetime.datetime.now(),
        reporter=r,
        editor=r,
        lang="es",
    )
    Article.objects.create(
        headline="Article Node 2",
        pub_date=datetime.date.today(),
        pub_date_time=datetime.datetime.now(),
        reporter=r,
        editor=r,
        lang="es",
    )
    Article.objects.create(
        headline="Article Node 3",
        pub_date=datetime.date.today(),
        pub_date_time=datetime.datetime.now(),
        reporter=r,
        editor=r,
        lang="en",
    )

    schema = graphene.Schema(query=Query)
    query = """
        query NodeFilteringQuery {
            allReporters {
                edges {
                    node {
                        id
                        articles(lang: "es", headline: "Article Node 1") {
                            edges {
                                node {
                                    id
                                }
                            }
                        }
                    }
                }
            }
        }
    """

    expected = {
        "allReporters": {
            "edges": [
                {
                    "node": {
                        "id": "UmVwb3J0ZXJUeXBlOjE=",
                        "articles": {
                            "edges": [{"node": {"id": "QXJ0aWNsZVR5cGU6MQ=="}}]
                        },
                    }
                }
            ]
        }
    }

    result = schema.execute(query)
    assert not result.errors
    assert result.data == expected


def test_should_enforce_first_or_last():
    graphene_settings.RELAY_CONNECTION_ENFORCE_FIRST_OR_LAST = True

    class ReporterType(DjangoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)

    class Query(graphene.ObjectType):
        all_reporters = DjangoConnectionField(ReporterType)

    r = Reporter.objects.create(
        first_name="John", last_name="Doe", email="johndoe@example.com", a_choice=1
    )

    schema = graphene.Schema(query=Query)
    query = """
        query NodeFilteringQuery {
            allReporters {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """

    expected = {"allReporters": None}

    result = schema.execute(query)
    assert len(result.errors) == 1
    assert str(result.errors[0]) == (
        "You must provide a `first` or `last` value to properly "
        "paginate the `allReporters` connection."
    )
    assert result.data == expected


def test_should_error_if_first_is_greater_than_max():
    graphene_settings.RELAY_CONNECTION_MAX_LIMIT = 100

    class ReporterType(DjangoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)

    class Query(graphene.ObjectType):
        all_reporters = DjangoConnectionField(ReporterType)

    r = Reporter.objects.create(
        first_name="John", last_name="Doe", email="johndoe@example.com", a_choice=1
    )

    schema = graphene.Schema(query=Query)
    query = """
        query NodeFilteringQuery {
            allReporters(first: 101) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """

    expected = {"allReporters": None}

    result = schema.execute(query)
    assert len(result.errors) == 1
    assert str(result.errors[0]) == (
        "Requesting 101 records on the `allReporters` connection "
        "exceeds the `first` limit of 100 records."
    )
    assert result.data == expected

    graphene_settings.RELAY_CONNECTION_ENFORCE_FIRST_OR_LAST = False


def test_should_error_if_last_is_greater_than_max():
    graphene_settings.RELAY_CONNECTION_MAX_LIMIT = 100

    class ReporterType(DjangoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)

    class Query(graphene.ObjectType):
        all_reporters = DjangoConnectionField(ReporterType)

    r = Reporter.objects.create(
        first_name="John", last_name="Doe", email="johndoe@example.com", a_choice=1
    )

    schema = graphene.Schema(query=Query)
    query = """
        query NodeFilteringQuery {
            allReporters(last: 101) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """

    expected = {"allReporters": None}

    result = schema.execute(query)
    assert len(result.errors) == 1
    assert str(result.errors[0]) == (
        "Requesting 101 records on the `allReporters` connection "
        "exceeds the `last` limit of 100 records."
    )
    assert result.data == expected

    graphene_settings.RELAY_CONNECTION_ENFORCE_FIRST_OR_LAST = False


def test_should_query_promise_connectionfields():
    from promise import Promise

    class ReporterType(DjangoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)

    class Query(graphene.ObjectType):
        all_reporters = DjangoConnectionField(ReporterType)

        def resolve_all_reporters(self, info, **args):
            return Promise.resolve([Reporter(id=1)])

    schema = graphene.Schema(query=Query)
    query = """
        query ReporterPromiseConnectionQuery {
            allReporters(first: 1) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """

    expected = {"allReporters": {"edges": [{"node": {"id": "UmVwb3J0ZXJUeXBlOjE="}}]}}

    result = schema.execute(query)
    assert not result.errors
    assert result.data == expected


def test_should_query_connectionfields_with_last():

    r = Reporter.objects.create(
        first_name="John", last_name="Doe", email="johndoe@example.com", a_choice=1
    )

    class ReporterType(DjangoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)

    class Query(graphene.ObjectType):
        all_reporters = DjangoConnectionField(ReporterType)

        def resolve_all_reporters(self, info, **args):
            return Reporter.objects.all()

    schema = graphene.Schema(query=Query)
    query = """
        query ReporterLastQuery {
            allReporters(last: 1) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """

    expected = {"allReporters": {"edges": [{"node": {"id": "UmVwb3J0ZXJUeXBlOjE="}}]}}

    result = schema.execute(query)
    assert not result.errors
    assert result.data == expected


def test_should_query_connectionfields_with_manager():

    r = Reporter.objects.create(
        first_name="John", last_name="Doe", email="johndoe@example.com", a_choice=1
    )

    r = Reporter.objects.create(
        first_name="John", last_name="NotDoe", email="johndoe@example.com", a_choice=1
    )

    class ReporterType(DjangoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)

    class Query(graphene.ObjectType):
        all_reporters = DjangoConnectionField(ReporterType, on="doe_objects")

        def resolve_all_reporters(self, info, **args):
            return Reporter.objects.all()

    schema = graphene.Schema(query=Query)
    query = """
        query ReporterLastQuery {
            allReporters(first: 2) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """

    expected = {"allReporters": {"edges": [{"node": {"id": "UmVwb3J0ZXJUeXBlOjE="}}]}}

    result = schema.execute(query)
    assert not result.errors
    assert result.data == expected


def test_should_query_dataloader_fields():
    from promise import Promise
    from promise.dataloader import DataLoader

    def article_batch_load_fn(keys):
        queryset = Article.objects.filter(reporter_id__in=keys)
        return Promise.resolve(
            [
                [article for article in queryset if article.reporter_id == id]
                for id in keys
            ]
        )

    article_loader = DataLoader(article_batch_load_fn)

    class ArticleType(DjangoObjectType):
        class Meta:
            model = Article
            interfaces = (Node,)

    class ReporterType(DjangoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)
            use_connection = True

        articles = DjangoConnectionField(ArticleType)

        def resolve_articles(self, info, **args):
            return article_loader.load(self.id)

    class Query(graphene.ObjectType):
        all_reporters = DjangoConnectionField(ReporterType)

    r = Reporter.objects.create(
        first_name="John", last_name="Doe", email="johndoe@example.com", a_choice=1
    )

    Article.objects.create(
        headline="Article Node 1",
        pub_date=datetime.date.today(),
        pub_date_time=datetime.datetime.now(),
        reporter=r,
        editor=r,
        lang="es",
    )
    Article.objects.create(
        headline="Article Node 2",
        pub_date=datetime.date.today(),
        pub_date_time=datetime.datetime.now(),
        reporter=r,
        editor=r,
        lang="en",
    )

    schema = graphene.Schema(query=Query)
    query = """
        query ReporterPromiseConnectionQuery {
            allReporters(first: 1) {
                edges {
                    node {
                        id
                        articles(first: 2) {
                            edges {
                                node {
                                    headline
                                }
                            }
                        }
                    }
                }
            }
        }
    """

    expected = {
        "allReporters": {
            "edges": [
                {
                    "node": {
                        "id": "UmVwb3J0ZXJUeXBlOjE=",
                        "articles": {
                            "edges": [
                                {"node": {"headline": "Article Node 1"}},
                                {"node": {"headline": "Article Node 2"}},
                            ]
                        },
                    }
                }
            ]
        }
    }

    result = schema.execute(query)
    assert not result.errors
    assert result.data == expected


def test_should_handle_inherited_choices():
    class BaseModel(models.Model):
        choice_field = models.IntegerField(choices=((0, "zero"), (1, "one")))

    class ChildModel(BaseModel):
        class Meta:
            proxy = True

    class BaseType(DjangoObjectType):
        class Meta:
            model = BaseModel

    class ChildType(DjangoObjectType):
        class Meta:
            model = ChildModel

    class Query(graphene.ObjectType):
        base = graphene.Field(BaseType)
        child = graphene.Field(ChildType)

    schema = graphene.Schema(query=Query)
    query = """
        query {
          child {
            choiceField
          }
        }
    """
    result = schema.execute(query)
    assert not result.errors


def test_proxy_model_support():
    """
    This test asserts that we can query for all Reporters,
    even if some are of a proxy model type at runtime.
    """

    class ReporterType(DjangoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)
            use_connection = True

    reporter_1 = Reporter.objects.create(
        first_name="John", last_name="Doe", email="johndoe@example.com", a_choice=1
    )

    reporter_2 = CNNReporter.objects.create(
        first_name="Some",
        last_name="Guy",
        email="someguy@cnn.com",
        a_choice=1,
        reporter_type=2,  # set this guy to be CNN
    )

    class Query(graphene.ObjectType):
        all_reporters = DjangoConnectionField(ReporterType)

    schema = graphene.Schema(query=Query)
    query = """
        query ProxyModelQuery {
            allReporters {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """

    expected = {
        "allReporters": {
            "edges": [
                {"node": {"id": "UmVwb3J0ZXJUeXBlOjE="}},
                {"node": {"id": "UmVwb3J0ZXJUeXBlOjI="}},
            ]
        }
    }

    result = schema.execute(query)
    assert not result.errors
    assert result.data == expected


def test_proxy_model_fails():
    """
    This test asserts that if you try to query for a proxy model,
    that query will fail with:
        GraphQLError('Expected value of type "CNNReporterType" but got:
            CNNReporter.',)

    This is because a proxy model has the identical model definition
    to its superclass, and defines its behavior at runtime, rather than
    at the database level. Currently, filtering objects of the proxy models'
    type isn't supported. It would require a field on the model that would
    represent the type, and it doesn't seem like there is a clear way to
    enforce this pattern across all projects
    """

    class CNNReporterType(DjangoObjectType):
        class Meta:
            model = CNNReporter
            interfaces = (Node,)
            use_connection = True

    reporter_1 = Reporter.objects.create(
        first_name="John", last_name="Doe", email="johndoe@example.com", a_choice=1
    )

    reporter_2 = CNNReporter.objects.create(
        first_name="Some",
        last_name="Guy",
        email="someguy@cnn.com",
        a_choice=1,
        reporter_type=2,  # set this guy to be CNN
    )

    class Query(graphene.ObjectType):
        all_reporters = DjangoConnectionField(CNNReporterType)

    schema = graphene.Schema(query=Query)
    query = """
        query ProxyModelQuery {
            allReporters {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """

    expected = {
        "allReporters": {
            "edges": [
                {"node": {"id": "UmVwb3J0ZXJUeXBlOjE="}},
                {"node": {"id": "UmVwb3J0ZXJUeXBlOjI="}},
            ]
        }
    }

    result = schema.execute(query)
    assert result.errors

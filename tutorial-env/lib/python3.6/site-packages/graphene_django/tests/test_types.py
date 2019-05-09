from mock import patch

from graphene import Interface, ObjectType, Schema, Connection, String
from graphene.relay import Node

from .. import registry
from ..types import DjangoObjectType, DjangoObjectTypeOptions
from .models import Article as ArticleModel
from .models import Reporter as ReporterModel

registry.reset_global_registry()


class Reporter(DjangoObjectType):
    """Reporter description"""

    class Meta:
        model = ReporterModel


class ArticleConnection(Connection):
    """Article Connection"""

    test = String()

    def resolve_test():
        return "test"

    class Meta:
        abstract = True


class Article(DjangoObjectType):
    """Article description"""

    class Meta:
        model = ArticleModel
        interfaces = (Node,)
        connection_class = ArticleConnection


class RootQuery(ObjectType):
    node = Node.Field()


schema = Schema(query=RootQuery, types=[Article, Reporter])


def test_django_interface():
    assert issubclass(Node, Interface)
    assert issubclass(Node, Node)


@patch("graphene_django.tests.models.Article.objects.get", return_value=Article(id=1))
def test_django_get_node(get):
    article = Article.get_node(None, 1)
    get.assert_called_with(pk=1)
    assert article.id == 1


def test_django_objecttype_map_correct_fields():
    fields = Reporter._meta.fields
    fields = list(fields.keys())
    assert fields[:-2] == [
        "id",
        "first_name",
        "last_name",
        "email",
        "pets",
        "a_choice",
        "reporter_type",
    ]
    assert sorted(fields[-2:]) == ["articles", "films"]


def test_django_objecttype_with_node_have_correct_fields():
    fields = Article._meta.fields
    assert list(fields.keys()) == [
        "id",
        "headline",
        "pub_date",
        "pub_date_time",
        "reporter",
        "editor",
        "lang",
        "importance",
    ]


def test_django_objecttype_with_custom_meta():
    class ArticleTypeOptions(DjangoObjectTypeOptions):
        """Article Type Options"""

    class ArticleType(DjangoObjectType):
        class Meta:
            abstract = True

        @classmethod
        def __init_subclass_with_meta__(cls, **options):
            options.setdefault("_meta", ArticleTypeOptions(cls))
            super(ArticleType, cls).__init_subclass_with_meta__(**options)

    class Article(ArticleType):
        class Meta:
            model = ArticleModel

    assert isinstance(Article._meta, ArticleTypeOptions)


def test_schema_representation():
    expected = """
schema {
  query: RootQuery
}

type Article implements Node {
  id: ID!
  headline: String!
  pubDate: Date!
  pubDateTime: DateTime!
  reporter: Reporter!
  editor: Reporter!
  lang: ArticleLang!
  importance: ArticleImportance
}

type ArticleConnection {
  pageInfo: PageInfo!
  edges: [ArticleEdge]!
  test: String
}

type ArticleEdge {
  node: Article
  cursor: String!
}

enum ArticleImportance {
  A_1
  A_2
}

enum ArticleLang {
  ES
  EN
}

scalar Date

scalar DateTime

interface Node {
  id: ID!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

type Reporter {
  id: ID!
  firstName: String!
  lastName: String!
  email: String!
  pets: [Reporter]
  aChoice: ReporterAChoice!
  reporterType: ReporterReporterType
  articles(before: String, after: String, first: Int, last: Int): ArticleConnection
}

enum ReporterAChoice {
  A_1
  A_2
}

enum ReporterReporterType {
  A_1
  A_2
}

type RootQuery {
  node(id: ID!): Node
}
""".lstrip()
    assert str(schema) == expected


def with_local_registry(func):
    def inner(*args, **kwargs):
        old = registry.get_global_registry()
        registry.reset_global_registry()
        try:
            retval = func(*args, **kwargs)
        except Exception as e:
            registry.registry = old
            raise e
        else:
            registry.registry = old
            return retval

    return inner


@with_local_registry
def test_django_objecttype_only_fields():
    class Reporter(DjangoObjectType):
        class Meta:
            model = ReporterModel
            only_fields = ("id", "email", "films")

    fields = list(Reporter._meta.fields.keys())
    assert fields == ["id", "email", "films"]


@with_local_registry
def test_django_objecttype_exclude_fields():
    class Reporter(DjangoObjectType):
        class Meta:
            model = ReporterModel
            exclude_fields = "email"

    fields = list(Reporter._meta.fields.keys())
    assert "email" not in fields

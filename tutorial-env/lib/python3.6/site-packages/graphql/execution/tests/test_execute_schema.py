# type: ignore

from graphql.execution import execute
from graphql.language.parser import parse
from graphql.type import (
    GraphQLArgument,
    GraphQLBoolean,
    GraphQLField,
    GraphQLID,
    GraphQLInt,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
)


def test_executes_using_a_schema():
    # type: () -> None
    BlogImage = GraphQLObjectType(
        "BlogImage",
        {
            "url": GraphQLField(GraphQLString),
            "width": GraphQLField(GraphQLInt),
            "height": GraphQLField(GraphQLInt),
        },
    )

    BlogAuthor = GraphQLObjectType(
        "Author",
        lambda: {
            "id": GraphQLField(GraphQLString),
            "name": GraphQLField(GraphQLString),
            "pic": GraphQLField(
                BlogImage,
                args={
                    "width": GraphQLArgument(GraphQLInt),
                    "height": GraphQLArgument(GraphQLInt),
                },
                resolver=lambda obj, info, **args: obj.pic(
                    args["width"], args["height"]
                ),
            ),
            "recentArticle": GraphQLField(BlogArticle),
        },
    )

    BlogArticle = GraphQLObjectType(
        "Article",
        {
            "id": GraphQLField(GraphQLNonNull(GraphQLString)),
            "isPublished": GraphQLField(GraphQLBoolean),
            "author": GraphQLField(BlogAuthor),
            "title": GraphQLField(GraphQLString),
            "body": GraphQLField(GraphQLString),
            "keywords": GraphQLField(GraphQLList(GraphQLString)),
        },
    )

    BlogQuery = GraphQLObjectType(
        "Query",
        {
            "article": GraphQLField(
                BlogArticle,
                args={"id": GraphQLArgument(GraphQLID)},
                resolver=lambda obj, info, **args: Article(args["id"]),
            ),
            "feed": GraphQLField(
                GraphQLList(BlogArticle),
                resolver=lambda *_: map(Article, range(1, 10 + 1)),
            ),
        },
    )

    BlogSchema = GraphQLSchema(BlogQuery)

    class Article(object):
        def __init__(self, id):
            # type: (int) -> None
            self.id = id
            self.isPublished = True
            self.author = Author()
            self.title = "My Article {}".format(id)
            self.body = "This is a post"
            self.hidden = "This data is not exposed in the schema"
            self.keywords = ["foo", "bar", 1, True, None]

    class Author(object):
        id = 123
        name = "John Smith"

        def pic(self, width, height):
            # type: (int, int) -> Pic
            return Pic(123, width, height)

        @property
        def recentArticle(self):
            # type: () -> Article
            return Article(1)

    class Pic(object):
        def __init__(self, uid, width, height):
            # type: (int, int, int) -> None
            self.url = "cdn://{}".format(uid)
            self.width = str(width)
            self.height = str(height)

    request = """
    {
        feed {
          id,
          title
        },
        article(id: "1") {
          ...articleFields,
          author {
            id,
            name,
            pic(width: 640, height: 480) {
              url,
              width,
              height
            },
            recentArticle {
              ...articleFields,
              keywords
            }
          }
        }
      }
      fragment articleFields on Article {
        id,
        isPublished,
        title,
        body,
        hidden,
        notdefined
      }
    """

    # Note: this is intentionally not validating to ensure appropriate
    # behavior occurs when executing an invalid query.
    result = execute(BlogSchema, parse(request))
    assert not result.errors
    assert result.data == {
        "feed": [
            {"id": "1", "title": "My Article 1"},
            {"id": "2", "title": "My Article 2"},
            {"id": "3", "title": "My Article 3"},
            {"id": "4", "title": "My Article 4"},
            {"id": "5", "title": "My Article 5"},
            {"id": "6", "title": "My Article 6"},
            {"id": "7", "title": "My Article 7"},
            {"id": "8", "title": "My Article 8"},
            {"id": "9", "title": "My Article 9"},
            {"id": "10", "title": "My Article 10"},
        ],
        "article": {
            "id": "1",
            "isPublished": True,
            "title": "My Article 1",
            "body": "This is a post",
            "author": {
                "id": "123",
                "name": "John Smith",
                "pic": {"url": "cdn://123", "width": 640, "height": 480},
                "recentArticle": {
                    "id": "1",
                    "isPublished": True,
                    "title": "My Article 1",
                    "body": "This is a post",
                    "keywords": ["foo", "bar", "1", "true", None],
                },
            },
        },
    }

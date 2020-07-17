from django.conf import settings
from django.shortcuts import render

from ..graphql.views import API_PATH, GraphQLView

EXAMPLE_QUERY = """# Welcome to Saleor GraphQL API!
#
# Type queries into this side of the screen, and you will see
# intelligent typeaheads aware of the current GraphQL type schema
# and live syntax and validation errors highlighted within the text.
#
# Here is an example query to fetch a list of products:
#
{
  products(first: 5, channel: "%(channel_slug)s") {
    edges {
      node {
        id
        name
        description
      }
    }
  }
}
""" % {
    "channel_slug": settings.DEFAULT_CHANNEL_SLUG
}


class DemoGraphQLView(GraphQLView):
    def render_playground(self, request):
        ctx = {
            "query": EXAMPLE_QUERY,
            "api_url": request.build_absolute_uri(str(API_PATH)),
        }
        return render(request, "graphql/playground.html", ctx)

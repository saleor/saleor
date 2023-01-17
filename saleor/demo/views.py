from django.conf import settings
from django.shortcuts import render

from ..graphql.views import GraphQLView

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
        pwa_origin = settings.PWA_ORIGINS[0]  # type: ignore[misc] # set only in demo settings # noqa: E501
        ctx = {
            "query": EXAMPLE_QUERY,
            "api_url": f"https://{pwa_origin}/graphql/",
        }
        return render(request, "graphql/playground.html", ctx)

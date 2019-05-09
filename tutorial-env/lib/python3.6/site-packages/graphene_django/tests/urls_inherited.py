from django.conf.urls import url

from ..views import GraphQLView
from .schema_view import schema


class CustomGraphQLView(GraphQLView):
    schema = schema
    graphiql = True
    pretty = True


urlpatterns = [url(r"^graphql/inherited/$", CustomGraphQLView.as_view())]

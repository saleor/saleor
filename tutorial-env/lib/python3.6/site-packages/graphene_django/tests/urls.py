from django.conf.urls import url

from ..views import GraphQLView

urlpatterns = [
    url(r"^graphql/batch", GraphQLView.as_view(batch=True)),
    url(r"^graphql", GraphQLView.as_view(graphiql=True)),
]

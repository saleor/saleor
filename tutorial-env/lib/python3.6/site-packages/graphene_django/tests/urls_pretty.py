from django.conf.urls import url

from ..views import GraphQLView
from .schema_view import schema

urlpatterns = [url(r"^graphql", GraphQLView.as_view(schema=schema, pretty=True))]

from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from ..graphql.api import schema
from ..urls import urlpatterns as core_urlpatterns
from .views import DemoGraphQLView

urlpatterns = [
    path("graphql/", csrf_exempt(DemoGraphQLView.as_view(schema=schema)), name="api"),
]

urlpatterns += core_urlpatterns

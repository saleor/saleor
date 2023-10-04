from ajax_select import urls as ajax_select_urls
from django.conf import settings
from django.urls import re_path, include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps import views
from django.contrib.staticfiles.views import serve
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from saleor.graphql.views import PrivateGraphQLView

# from saleor.graphql.views import AuthGraphQLView
from .core.sitemaps import sitemaps
from .search.urls import urlpatterns as search_urls


# def graphql_token_view():
#     view = csrf_exempt(AuthGraphQLView.as_view(graphiql=settings.DEBUG))
#     return view

from saleor_oye.api.graphql import schema


urlpatterns = [
    # re_path(r'^graphql', graphql_token_view()),
    re_path(r'^graphql', csrf_exempt(PrivateGraphQLView.as_view(graphiql=True, schema=schema))),
    # re_path(r'^graphiql', include('django_graphiql.urls')),
    re_path(r'^search/', include((search_urls, 'search'), namespace='search')),
    re_path(r'^sitemap\.xml$', views.index, {'sitemaps': sitemaps}),
    re_path(r'^sitemap-(?P<section>.+)\.xml$', views.sitemap, {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap'),

    re_path(r'^robots\.txt', include('robots.urls')),

    re_path(r'^oye/', include('saleor_oye.urls')),
    re_path(r'^admin/', admin.site.urls),
    # place it at whatever base url you like
    re_path(r'^ajax_select/', include(ajax_select_urls)),
]

if settings.DEBUG:
    # static files (images, css, javascript, etc.)
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve)
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

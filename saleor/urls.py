from ajax_select import urls as ajax_select_urls
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps import views
from django.contrib.sitemaps.views import sitemap
from django.contrib.staticfiles.views import serve
from django.views.decorators.csrf import csrf_exempt

from saleor.graphql.views import AuthGraphQLView
from .core.sitemaps import sitemaps
from .search.urls import urlpatterns as search_urls


def graphql_token_view():
    # view = GraphQLView.as_view(graphiql=settings.DEBUG)
    # view = csrf_exempt(GraphQLView.as_view(graphiql=settings.DEBUG))
    view = csrf_exempt(AuthGraphQLView.as_view(graphiql=settings.DEBUG))
    # view = permission_classes((AllowAny, ))(view)
    # view = authentication_classes((JSONWebTokenAuthentication,))(view)
    # view = api_view(['POST'])(view)
    return view

urlpatterns = [
    # url(r'^account/', include('allauth.urls')),
    # url(r'^account/login', login_view, name="account_login"),
    url(r'^graphql', graphql_token_view()),
    url(r'^graphiql', include('django_graphiql.urls')),
    url(r'^search/', include(search_urls, namespace='search')),
    url(r'^sitemap\.xml$', views.index, {'sitemaps': sitemaps}),
    url(r'^sitemap-(?P<section>.+)\.xml$', views.sitemap, {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap'),

    # url(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps},
    #     name='django.contrib.sitemaps.views.sitemap'),
    url(r'^oye/', include('saleor_oye.urls', namespace='oye')),
    url(r'^admin/', include(admin.site.urls)),
    # place it at whatever base url you like
    url(r'^ajax_select/', include(ajax_select_urls)),
    # url(r'', include('payments.urls')),
]

if settings.DEBUG:
    # static files (images, css, javascript, etc.)
    urlpatterns += [
        url(r'^static/(?P<path>.*)$', serve)
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

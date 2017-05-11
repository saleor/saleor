from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.contrib.staticfiles.views import serve
from django.views.decorators.csrf import csrf_exempt
from django.views.i18n import javascript_catalog
from graphene_django.views import GraphQLView
from rest_framework.decorators import permission_classes, authentication_classes, api_view
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from saleor_oye.auth.backends import OyeTokenAuth

from saleor_oye.cart.urls import urlpatterns as oye_cart_urls

from .checkout.urls import urlpatterns as checkout_urls
from .core.sitemaps import sitemaps
from .dashboard.urls import urlpatterns as dashboard_urls
from .data_feeds.urls import urlpatterns as feed_urls
from .order.urls import urlpatterns as order_urls
from .product.urls import urlpatterns as product_urls
from .search.urls import urlpatterns as search_urls
from .userprofile.urls import urlpatterns as userprofile_urls
from .userprofile.views import login as login_view


from ajax_select import urls as ajax_select_urls


def graphql_token_view():
    view = csrf_exempt(GraphQLView.as_view(graphiql=settings.DEBUG))
    view = authentication_classes((JSONWebTokenAuthentication,))(view)
    view = api_view(['POST'])(view)
    return view

urlpatterns = [
    # url(r'^', include(core_urls)),
    url(r'^account/', include('allauth.urls')),
    url(r'^account/login', login_view, name="account_login"),
    # url(r'^cart/', include(oye_cart_urls, namespace='cart')),
    # url(r'^checkout/', include(checkout_urls, namespace='checkout')),
    # url(r'^dashboard/', include(dashboard_urls, namespace='dashboard')),
    url(r'^graphql', graphql_token_view()),
    url(r'^graphiql', csrf_exempt(GraphQLView.as_view(graphiql=settings.DEBUG))),
    # url(r'^jsi18n/$', javascript_catalog, name='javascript-catalog'),
    # url(r'^order/', include(order_urls, namespace='order')),
    # url(r'^products/', include(product_urls, namespace='product')),
    # url(r'^profile/', include(userprofile_urls, namespace='profile')),
    url(r'^search/', include(search_urls, namespace='search')),
    # url(r'^feeds/', include(feed_urls, namespace='data_feeds')),
    url(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap'),
    url(r'^oye/', include('saleor_oye.urls', namespace='oye')),
    url(r'^admin/', include(admin.site.urls)),
    # place it at whatever base url you like
    url(r'^ajax_select/', include(ajax_select_urls)),
    url(r'', include('payments.urls')),
]

if settings.DEBUG:
    # static files (images, css, javascript, etc.)
    urlpatterns += [
        url(r'^static/(?P<path>.*)$', serve)
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

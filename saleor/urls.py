from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.contrib.staticfiles.views import serve
from django.views.decorators.csrf import csrf_exempt
from django.views.i18n import JavaScriptCatalog, set_language

from .core.sitemaps import sitemaps
from .data_feeds.urls import urlpatterns as feed_urls
from .graphql.api import schema
from .graphql.views import GraphQLView
from .product.views import digital_product

non_translatable_urlpatterns = [
    url(r"^graphql/", csrf_exempt(GraphQLView.as_view(schema=schema)), name="api"),
    url(
        r"^sitemap\.xml$",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    url(r"^i18n/$", set_language, name="set_language"),
    url("", include("social_django.urls", namespace="social")),
]

translatable_urlpatterns = [
    url(r"^jsi18n/$", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    url(r"^feeds/", include((feed_urls, "data_feeds"), namespace="data_feeds")),
    url(
        r"^digital-download/(?P<token>[0-9A-Za-z_\-]+)/$",
        digital_product,
        name="digital-product",
    ),
]

urlpatterns = non_translatable_urlpatterns + i18n_patterns(*translatable_urlpatterns)

if settings.DEBUG:
    try:
        import debug_toolbar
    except ImportError:
        """The debug toolbar was not installed. Ignore the error.
        settings.py should already have warned the user about it."""
    else:
        urlpatterns += [url(r"^__debug__/", include(debug_toolbar.urls))]

    urlpatterns += [
        # static files (images, css, javascript, etc.)
        url(r"^static/(?P<path>.*)$", serve)
    ] + static("/media/", document_root=settings.MEDIA_ROOT)

if settings.ENABLE_SILK:
    urlpatterns += [url(r"^silk/", include("silk.urls", namespace="silk"))]

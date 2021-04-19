from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib.staticfiles.views import serve
from django.urls import path, re_path
from django.views.decorators.csrf import csrf_exempt

from .graphql.api import schema
from .graphql.views import GraphQLView
from .plugins.views import handle_plugin_webhook
from .product.views import digital_product

urlpatterns = [
    path("graphql/", csrf_exempt(GraphQLView.as_view(schema=schema)), name="api"),
    path("digital-download/<slug:token>/", digital_product, name="digital-product"),
    path("plugins/<slug:plugin_id>/", handle_plugin_webhook, name="plugins"),
]

if settings.DEBUG:
    import warnings

    from .core import views

    try:
        import debug_toolbar
    except ImportError:
        warnings.warn(
            "The debug toolbar was not installed. Ignore the error. \
            settings.py should already have warned the user about it."
        )
    else:
        urlpatterns += [
            path("__debug__/", include(debug_toolbar.urls))  # type: ignore
        ]

    urlpatterns += static("/media/", document_root=settings.MEDIA_ROOT) + [
        re_path(r"^static/(?P<path>.*)$", serve),
        path("", views.home, name="home"),
    ]

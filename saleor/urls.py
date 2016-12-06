from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.contrib.staticfiles.views import serve

from .cart.urls import urlpatterns as cart_urls
from .checkout.urls import urlpatterns as checkout_urls
from .core.sitemaps import sitemaps
from .core.urls import urlpatterns as core_urls
from .order.urls import urlpatterns as order_urls
from .product.urls import urlpatterns as product_urls
from .search.urls import urlpatterns as search_urls
from .userprofile.urls import urlpatterns as userprofile_urls
from .data_feeds.urls import urlpatterns as feed_urls
from .dashboard.urls import urlpatterns as dashboard_urls


admin.autodiscover()

urlpatterns = [
    url(r'^', include(core_urls)),
    url(r'^account/', include('allauth.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^cart/', include(cart_urls, namespace='cart')),
    url(r'^checkout/', include(checkout_urls, namespace='checkout')),
    url(r'^dashboard/', include(dashboard_urls, namespace='dashboard')),
    url(r'^order/', include(order_urls, namespace='order')),
    url(r'^products/', include(product_urls, namespace='product')),
    url(r'^profile/', include(userprofile_urls, namespace='profile')),
    url(r'^search/', include(search_urls, namespace='search')),
    url(r'^selectable/', include('selectable.urls')),
    url(r'^feeds/', include(feed_urls, namespace='data_feeds')),
    url(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap'),
    url(r'', include('payments.urls'))
]

if settings.DEBUG:
    # static files (images, css, javascript, etc.)
    urlpatterns += [
        url(r'^static/(?P<path>.*)$', serve)
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

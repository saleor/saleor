from django.conf import settings
from django.conf.urls import patterns, url, include
from django.contrib import admin


admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', 'saleor.views.home', name='home'),
    url(r'^account/', include('registration.urls', namespace='registration')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^cart/', include('cart.urls', namespace='cart')),
    url(r'^checkout/', include('checkout.urls', namespace='checkout')),
    url(r'^images/', include('django_images.urls')),
    url(r'^order/', include('order.urls', namespace='order')),
    url(r'^products/', include('product.urls', namespace='product')),
    url(r'^profile/', include('userprofile.urls', namespace='profile')),
    url(r'^', include('payments.urls'))
)

if settings.DEBUG:
    # static files (images, css, javascript, etc.)
    urlpatterns += patterns(
        '',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}))

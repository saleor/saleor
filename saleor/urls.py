from django.conf.urls import patterns, url, include
from django.contrib import admin


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', 'saleor.views.home', name='home'),
    url(r'^products/', include('product.urls', namespace='product')),
    url(r'^order/', include('order.urls', namespace='order')),
    url(r'^cart/', include('cart.urls', namespace='cart')),
)

from django.conf.urls import include, url

from . import views
from .checkout.urls import urlpatterns as checkout_urls

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^update/(?P<variant_id>\d+)/$', views.update, name='update-line'),
    url(r'^summary/$', views.summary, name='cart-summary'),
    url(r'^shipping-options/$', views.get_shipping_options,
        name='shipping-options'),
    url(r'^checkout/', include(checkout_urls))]

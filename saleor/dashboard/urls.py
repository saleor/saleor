from django.conf.urls import patterns, url, include
from . import views as core_views

from order.urls import urlpatterns as order_urls
from product.urls import urlpatterns as product_urls
from payments.urls import urlpatterns as payments_urls
from customer.urls import urlpatterns as customer_urls


urlpatterns = patterns('',
                       url(r'^$', core_views.index, name='index'),
                       url(r'^orders/', include(order_urls)),
                       url(r'^products/', include(product_urls)),
                       url(r'^payments/', include(payments_urls)),
                       url(r'^customers/', include(customer_urls)),
)

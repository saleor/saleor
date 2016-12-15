from django.conf.urls import url, include

from . import views as core_views
from .category.urls import urlpatterns as category_urls
from .customer.urls import urlpatterns as customer_urls
from .order.urls import urlpatterns as order_urls
from .payments.urls import urlpatterns as payments_urls
from .product.urls import urlpatterns as product_urls
from .discount.urls import urlpatterns as discount_urls
from .search.urls import urlpatterns as search_urls
from .shipping.urls import urlpatterns as shipping_urls


urlpatterns = [
    url(r'^$', core_views.index, name='index'),
    url(r'^categories/', include(category_urls)),
    url(r'^orders/', include(order_urls)),
    url(r'^products/', include(product_urls)),
    url(r'^payments/', include(payments_urls)),
    url(r'^customers/', include(customer_urls)),
    url(r'^discounts/', include(discount_urls)),
    url(r'^search/', include(search_urls)),
    url(r'^shipping/', include(shipping_urls)),
]

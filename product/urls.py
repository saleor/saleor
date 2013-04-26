from django.conf.urls import patterns, url


urlpatterns = patterns('product.views',
    url(r'^(?P<slug>[a-z0-9-]+?)-(?P<product_id>[0-9]+)/$', 'product_details',
        name='details'),
    url(r'^category/(?P<slug>[a-z0-9-]+?)/$', 'category_index',
        name='category')
)

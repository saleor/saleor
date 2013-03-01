from django.conf.urls import patterns, url


urlpatterns = patterns('cart.views',
    url(r'^$', 'index', name='index'),
)


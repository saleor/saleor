from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.shipping_method_list, name='shipping-methods'),
    url(r'^add/$', views.shipping_method_add, name='shipping-method-add'),
    url(r'^(?P<pk>\d+)/$', views.shipping_method_detail, name='shipping-method-detail'),
    url(r'^(?P<pk>\d+)/delete/$',
        views.shipping_method_delete, name='shipping-method-delete'),
]

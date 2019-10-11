from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^$", views.index, name="payments-index"),
    url(
        r"^configure/(?P<plugin_name>[\w-]+)$",
        views.configure_payment_gateway,
        name="configure-payment",
    ),
]

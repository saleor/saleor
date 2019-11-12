from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^$", views.index, name="warehouse-list"),
    url(r"^create$", views.warehouse_create, name="warehouse-create"),
    url(
        r"^update/(?P<uuid>[0-9a-f-]+)$",
        views.warehouse_update,
        name="warehouse-update",
    ),
    url(r"^(?P<uuid>[0-9a-f-]+)$", views.warehouse, name="warehouse-detail"),
    url(
        r"^delete/(?P<uuid>[0-9a-f-]+)$",
        views.warehouse_delete,
        name="warehouse-delete",
    ),
]

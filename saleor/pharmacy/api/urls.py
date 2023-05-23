from django.urls import path

from .views import HealthProfileList

urlpatterns = [
    path(
        "users/health-profiles/<uuid:uuid>",
        HealthProfileList.as_view(),
        name="hp-detail",
    )
]

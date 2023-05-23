from django.urls import path

from .views import HealthProfilesDetail

urlpatterns = [
    path(
        "users/health-profiles/<uuid:uuid>",
        HealthProfilesDetail.as_view(),
        name="hp-detail",
    )
]

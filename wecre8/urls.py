from django.conf.urls import url

from wecre8.views import apple_aasa

urlpatterns = [
    url(
        r"^.well-known/apple-developer-merchantid-domain-association.txt",
        apple_aasa,
        name="apple_static",
    ),
]

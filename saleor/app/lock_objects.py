from django.db.models import QuerySet

from .models import App


def app_qs_select_for_update() -> QuerySet[App]:
    return App.objects.order_by("pk").select_for_update(of=["self"])

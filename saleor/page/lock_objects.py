from django.db.models import QuerySet

from .models import Page


def page_qs_select_for_update() -> QuerySet[Page]:
    return Page.objects.order_by("pk").select_for_update(of=(["self"]))

from django.db.models import QuerySet

from .models import BaseMedia


def media_qs_select_for_update(model: type[BaseMedia]) -> QuerySet:
    """Lock a gallery's rows in primary key order, one media model at a time."""
    return model.objects.order_by("pk").select_for_update(of=["self"])

from django.db.models import QuerySet


def queryset_in_batches(queryset: QuerySet, batch_size: int):
    """Slice a queryset into batches."""
    start_pk = 0

    while True:
        qs = queryset.filter(pk__gt=start_pk).order_by("pk")[:batch_size]
        pks = list(qs.values_list("pk", flat=True))

        if not pks:
            break

        yield pks

        start_pk = pks[-1]

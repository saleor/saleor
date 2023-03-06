from django.utils import timezone

from ..core.enums import ReportingPeriod


def reporting_period_to_date(period):
    now = timezone.now()
    if period == ReportingPeriod.TODAY:
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == ReportingPeriod.THIS_MONTH:
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        raise ValueError(f"Unknown period: {period}")
    return start_date


def filter_by_period(queryset, period, field_name):
    start_date = reporting_period_to_date(period)
    return queryset.filter(**{f"{field_name}__gte": start_date})


def filter_range_field(qs, field, value):
    gte, lte = value.get("gte"), value.get("lte")
    if gte is not None:
        lookup = {f"{field}__gte": gte}
        qs = qs.filter(**lookup)
    if lte is not None:
        lookup = {f"{field}__lte": lte}
        qs = qs.filter(**lookup)
    return qs


def filter_by_id(object_type):
    from . import resolve_global_ids_to_primary_keys

    def inner(qs, _, value):
        if not value:
            return qs
        _, obj_pks = resolve_global_ids_to_primary_keys(value, object_type)
        return qs.filter(id__in=obj_pks)

    return inner

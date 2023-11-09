from decimal import Decimal
from typing import TYPE_CHECKING, Union

from django.utils import timezone

from ..core.enums import ReportingPeriod

if TYPE_CHECKING:
    from django.db.models import QuerySet

Number = Union[float, int, Decimal]


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
    """Use only in standard filters.

    Returns entering qs when value is empty.
    """
    from . import resolve_global_ids_to_primary_keys

    def inner(qs, _, value):
        if not value:
            return qs
        _, obj_pks = resolve_global_ids_to_primary_keys(value, object_type)
        return qs.filter(id__in=obj_pks)

    return inner


def filter_by_ids(object_type):
    """Use in where filters.

    Returns empty qs when value is empty.
    """
    from . import resolve_global_ids_to_primary_keys

    def inner(qs, _, value):
        _, obj_pks = resolve_global_ids_to_primary_keys(value, object_type)
        return qs.filter(id__in=obj_pks)

    return inner


def filter_where_range_field(qs, field, value):
    if value is None:
        return qs.none()
    range = value.get("range")
    if range:
        gte, lte = range.get("gte"), range.get("lte")
        if gte is None and lte is None:
            return qs.none()
        return filter_range_field(qs, field, range)
    if "eq" in value:
        # allow filtering by `None` value
        return qs.filter(**{field: value["eq"]})
    if one_of := value.get("one_of"):
        return qs.filter(**{f"{field}__in": one_of})
    return qs.none()


def filter_where_by_string_field(
    qs: "QuerySet", field: str, value: dict[str, Union[str, list[str]]]
):
    if value is None:
        return qs.none()
    if "eq" in value:
        # allow filtering by `None` value
        return qs.filter(**{field: value["eq"]})
    if one_of := value.get("one_of"):
        return qs.filter(**{f"{field}__in": one_of})
    return qs.none()


def filter_where_by_id_field(
    qs: "QuerySet", field: str, value: dict[str, Union[str, list[str]]], type: str
):
    from . import resolve_global_ids_to_primary_keys

    eq = value.get("eq")
    one_of = value.get("one_of")
    if eq and isinstance(eq, str):
        _, pks = resolve_global_ids_to_primary_keys([eq], type, True)
        return qs.filter(**{field: pks[0]})
    if one_of:
        _, pks = resolve_global_ids_to_primary_keys(one_of, type, True)
        return qs.filter(**{f"{field}__in": pks})
    return qs.none()


def filter_where_by_numeric_field(
    qs: "QuerySet",
    field: str,
    value: dict[str, Union[Number, list[Number], dict[str, Number]]],
):
    one_of = value.get("one_of")
    range = value.get("range")

    if "eq" in value:
        # allow filtering by `None` value
        return qs.filter(**{field: value["eq"]})
    if one_of:
        return qs.filter(**{f"{field}__in": one_of})
    if range and isinstance(range, dict):
        lte = range.get("lte")
        gte = range.get("gte")
        if lte is None and gte is None:
            return qs.none()
        if lte is not None:
            qs = qs.filter(**{f"{field}__lte": lte})
        if gte is not None:
            qs = qs.filter(**{f"{field}__gte": gte})
        return qs
    return qs.none()

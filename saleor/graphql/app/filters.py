import django_filters

from ...app import models
from ...app.types import AppType
from ..core.filters import EnumFilter
from ..utils.filters import filter_by_query_param
from .enums import AppTypeEnum


def filter_app_search(qs, _, value):
    if value:
        qs = filter_by_query_param(qs, value, ("name",))
    return qs


def filter_type(qs, _, value):
    if value in [AppType.LOCAL, AppType.THIRDPARTY]:
        qs = qs.filter(type=value)
    return qs


class AppFilter(django_filters.FilterSet):
    type = EnumFilter(input_class=AppTypeEnum, method=filter_type)
    search = django_filters.CharFilter(method=filter_app_search)
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = models.App
        fields = ["search", "is_active"]

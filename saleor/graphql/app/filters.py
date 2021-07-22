import django_filters

from ...app import models
from ...app.types import AppExtensionTarget, AppExtensionType, AppExtensionView, AppType
from ..core.filters import EnumFilter
from ..utils.filters import filter_by_query_param
from .enums import (
    AppExtensionTargetEnum,
    AppExtensionTypeEnum,
    AppExtensionViewEnum,
    AppTypeEnum,
)


def filter_app_search(qs, _, value):
    if value:
        qs = filter_by_query_param(qs, value, ("name",))
    return qs


def filter_app_type(qs, _, value):
    if value in [AppType.LOCAL, AppType.THIRDPARTY]:
        qs = qs.filter(type=value)
    return qs


def filter_app_extension_view(qs, _, value):
    if value in [view for view, _ in AppExtensionView.CHOICES]:
        qs = qs.filter(view=value)
    return qs


def filter_app_extension_type(qs, _, value):
    if value in [type for type, _ in AppExtensionType.CHOICES]:
        qs = qs.filter(type=value)
    return qs


def filter_app_extension_target(qs, _, value):
    if value in [target for target, _ in AppExtensionTarget.CHOICES]:
        qs = qs.filter(target=value)
    return qs


class AppFilter(django_filters.FilterSet):
    type = EnumFilter(input_class=AppTypeEnum, method=filter_app_type)
    search = django_filters.CharFilter(method=filter_app_search)
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = models.App
        fields = ["search", "is_active"]


class AppExtensionFilter(django_filters.FilterSet):
    view = EnumFilter(
        input_class=AppExtensionViewEnum, method=filter_app_extension_view
    )
    type = EnumFilter(
        input_class=AppExtensionTypeEnum, method=filter_app_extension_type
    )
    target = EnumFilter(
        input_class=AppExtensionTargetEnum, method=filter_app_extension_target
    )

    class Meta:
        model = models.AppExtension
        fields = [
            "view",
            "type",
            "target",
        ]

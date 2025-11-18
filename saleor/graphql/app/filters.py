import django_filters
import graphene

from ...app import models
from ...app.types import AppExtensionTarget, AppType
from ..core.descriptions import ADDED_IN_322, DEPRECATED_IN_3X_INPUT
from ..core.filters import EnumFilter, ListObjectTypeFilter
from .enums import AppExtensionMountEnum, AppExtensionTargetEnum, AppTypeEnum


def filter_app_search(qs, _, value):
    if value:
        qs = qs.filter(name__ilike=value)
    return qs


def filter_app_type(qs, _, value):
    if value in [AppType.LOCAL, AppType.THIRDPARTY]:
        qs = qs.filter(type=value)
    return qs


def filter_app_extension_target(qs, _, value):
    if value in [target for target, _ in AppExtensionTarget.CHOICES]:
        qs = qs.filter(target=value)
    return qs


def filter_app_extension_mount(qs, _, value):
    if value:
        qs = qs.filter(mount__in=value)
    return qs


def filter_app_extension_mount_name(qs, _, value):
    if value:
        qs = qs.filter(mount__in=[v.lower() for v in value])
    return qs


def filter_app_extension_target_name(qs, _, value):
    if value:
        qs = qs.filter(target=value.lower())
    return qs


class AppFilter(django_filters.FilterSet):
    type = EnumFilter(input_class=AppTypeEnum, method=filter_app_type)
    search = django_filters.CharFilter(method=filter_app_search)
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = models.App
        fields = ["search", "is_active"]


class AppExtensionFilter(django_filters.FilterSet):
    mount = ListObjectTypeFilter(
        input_class=AppExtensionMountEnum,
        method=filter_app_extension_mount,
        help_text=f"DEPRECATED: Use `mountName` instead. {DEPRECATED_IN_3X_INPUT}",
    )
    target = EnumFilter(
        input_class=AppExtensionTargetEnum,
        method=filter_app_extension_target,
        help_text=f"DEPRECATED: Use `targetName` instead. {DEPRECATED_IN_3X_INPUT}",
    )
    mountName = ListObjectTypeFilter(
        input_class=graphene.String,
        method=filter_app_extension_mount_name,
        help_text="Plain-text mount name (case insensitive)" + ADDED_IN_322,
    )
    targetName = django_filters.CharFilter(
        method=filter_app_extension_target_name,
        help_text="Plain-text target name (case insensitive)" + ADDED_IN_322,
    )

    class Meta:
        model = models.AppExtension
        fields = ["mount", "target", "mountName", "targetName"]

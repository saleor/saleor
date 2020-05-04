import django_filters

from ....app.models import App
from ..filters import filter_search


class ServiceAccountFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_search)
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = App
        fields = ["search", "is_active"]

from graphene_django.fields import DjangoConnectionField


class DistinctConnectionField(DjangoConnectionField):
    """Connection that allows combining two querysets, by making both of them
    distinct, if at least one of them is distinct."""

    @classmethod
    def merge_querysets(cls, default_queryset, queryset):
        if queryset.query.distinct or default_queryset.query.distinct:
            queryset = queryset.distinct()
            default_queryset = default_queryset.distinct()
        return queryset & default_queryset

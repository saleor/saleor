import graphene
from django.shortcuts import _get_queryset


def get_object_or_none(klass, *args, **kwargs):
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except AttributeError:
        klass__name = klass.__name__ if isinstance(klass, type) else klass.__class__.__name__
        raise ValueError(
            "First argument to get_object_or_none() must be a Model, Manager, "
            "or QuerySet, not '%s'." % klass__name
        )
    except queryset.model.DoesNotExist:
        return None


class DjangoPkInterface(graphene.Interface):
    """
    Exposes the Django model primary key
    """
    pk = graphene.ID(description="Primary key")

    def resolve_pk(self, args, context, info):
        return self.pk

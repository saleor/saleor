import itertools

from django.db import models
from django_filters.filterset import BaseFilterSet, FilterSet
from django_filters.filterset import FILTER_FOR_DBFIELD_DEFAULTS

from .global_id_filter import GlobalIDFilter, GlobalIDMultipleChoiceFilter


GRAPHENE_FILTER_SET_OVERRIDES = {
    models.AutoField: {"filter_class": GlobalIDFilter},
    models.OneToOneField: {"filter_class": GlobalIDFilter},
    models.ForeignKey: {"filter_class": GlobalIDFilter},
    models.ManyToManyField: {"filter_class": GlobalIDMultipleChoiceFilter},
    models.ManyToOneRel: {"filter_class": GlobalIDMultipleChoiceFilter},
    models.ManyToManyRel: {"filter_class": GlobalIDMultipleChoiceFilter},
}


class GrapheneFilterSetMixin(BaseFilterSet):
    """ A django_filters.filterset.BaseFilterSet with default filter overrides
    to handle global IDs """

    FILTER_DEFAULTS = dict(
        itertools.chain(
            FILTER_FOR_DBFIELD_DEFAULTS.items(), GRAPHENE_FILTER_SET_OVERRIDES.items()
        )
    )


def setup_filterset(filterset_class):
    """ Wrap a provided filterset in Graphene-specific functionality
    """
    return type(
        "Graphene{}".format(filterset_class.__name__),
        (filterset_class, GrapheneFilterSetMixin),
        {},
    )

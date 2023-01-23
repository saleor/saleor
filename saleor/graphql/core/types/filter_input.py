import itertools

import graphene
from django.db import models
from django_filters.filterset import FILTER_FOR_DBFIELD_DEFAULTS, BaseFilterSet
from graphene import Argument, InputField, InputObjectType, String
from graphene.types.inputobjecttype import InputObjectTypeOptions
from graphene.types.utils import yank_fields_from_attrs

from ..descriptions import ADDED_IN_311, DEPRECATED_IN_3X_INPUT, PREVIEW_FEATURE
from ..filters import GlobalIDFilter, GlobalIDMultipleChoiceFilter
from ..scalars import Date
from . import NonNullList
from .common import DateRangeInput, DateTimeRangeInput, IntRangeInput
from .converter import convert_form_field

GLOBAL_ID_FILTERS = {
    models.AutoField: {"filter_class": GlobalIDFilter},
    models.OneToOneField: {"filter_class": GlobalIDFilter},
    models.ForeignKey: {"filter_class": GlobalIDFilter},
    models.ManyToManyField: {"filter_class": GlobalIDMultipleChoiceFilter},
    models.ManyToOneRel: {"filter_class": GlobalIDMultipleChoiceFilter},
    models.ManyToManyRel: {"filter_class": GlobalIDMultipleChoiceFilter},
}


class GraphQLFilterSetMixin(BaseFilterSet):
    FILTER_DEFAULTS = dict(
        itertools.chain(FILTER_FOR_DBFIELD_DEFAULTS.items(), GLOBAL_ID_FILTERS.items())
    )


def get_filterset_class(filterset_class=None):
    return type(
        "GraphQL{}".format(filterset_class.__name__),
        (filterset_class, GraphQLFilterSetMixin),
        {},
    )


class FilterInputObjectType(InputObjectType):
    """Class for storing and serving django-filters as graphQL input.

    FilterSet class which inherits from django-filters.FilterSet should be
    provided with using fitlerset_class argument.
    """

    @classmethod
    def __init_subclass_with_meta__(
        cls, _meta=None, model=None, filterset_class=None, fields=None, **options
    ):
        cls.custom_filterset_class = filterset_class
        cls.filterset_class = None
        cls.fields = fields
        cls.model = model

        if not _meta:
            _meta = InputObjectTypeOptions(cls)

        fields = cls.get_filtering_args_from_filterset()
        fields = yank_fields_from_attrs(fields, _as=InputField)
        if _meta.fields:
            _meta.fields.update(fields)
        else:
            _meta.fields = fields

        super().__init_subclass_with_meta__(_meta=_meta, **options)

    @classmethod
    def get_filtering_args_from_filterset(cls):
        """Retrieve the filtering arguments from the queryset.

        Inspect a FilterSet and produce the arguments to pass to a Graphene field.
        These arguments will be available to filter against in the GraphQL.
        """
        if not cls.custom_filterset_class:
            raise ValueError("Provide filterset class")

        cls.filterset_class = get_filterset_class(cls.custom_filterset_class)

        args = {}
        for name, filter_field in cls.filterset_class.base_filters.items():
            input_class = getattr(filter_field, "input_class", None)
            if input_class:
                field_type = convert_form_field(filter_field)
            else:
                field_type = convert_form_field(filter_field.field)
                field_type.description = getattr(filter_field, "help_text", "")
            kwargs = getattr(field_type, "kwargs", {})
            field_type.kwargs = kwargs
            args[name] = field_type
        return args


class ChannelFilterInputObjectType(FilterInputObjectType):
    channel = Argument(
        String,
        description=(
            "Specifies the channel by which the data should be filtered. "
            f"{DEPRECATED_IN_3X_INPUT} Use root-level channel argument instead."
        ),
    )

    class Meta:
        abstract = True


class WhereInputObjectType(FilterInputObjectType):
    """Class for storing and serving django-filters with additional operators input.

    FilterSet class which inherits from django-filters.FilterSet should be
    provided with using fitlerset_class argument.

    AND, OR, and NOT class type fields are automatically added to available input
    fields, allowing to create complex filter statements.
    """

    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, _meta=None, **options):
        super().__init_subclass_with_meta__(_meta=_meta, **options)
        cls._meta.fields.update(
            {
                "AND": graphene.Field(
                    NonNullList(
                        cls,
                    ),
                    description="List of conditions that must be met.",
                ),
                "OR": graphene.Field(
                    NonNullList(
                        cls,
                    ),
                    description=(
                        "A list of conditions of which at least one must be met."
                    ),
                ),
                # TODO: needs optimization
                # "NOT": graphene.Field(
                #     cls, description="A condition that cannot be met."
                # ),
            }
        )


class FilterInputDescriptions:
    EQ = "The value equal to."
    ONE_OF = "The value included in."
    RANGE = "The value in range."


class StringFilterInput(graphene.InputObjectType):
    eq = graphene.String(description=FilterInputDescriptions.EQ, required=False)
    one_of = NonNullList(
        graphene.String,
        description=FilterInputDescriptions.ONE_OF,
        required=False,
    )

    class Meta:
        description = (
            "Define the filtering options for string fields."
            + ADDED_IN_311
            + PREVIEW_FEATURE
        )


class IntFilterInput(graphene.InputObjectType):
    eq = graphene.Int(description=FilterInputDescriptions.EQ, required=False)
    one_of = NonNullList(
        graphene.Int, description=FilterInputDescriptions.ONE_OF, required=False
    )
    range = IntRangeInput(description=FilterInputDescriptions.RANGE, required=False)

    class Meta:
        description = (
            "Define the filtering options for integer fields."
            + ADDED_IN_311
            + PREVIEW_FEATURE
        )


class DateFilterInput(graphene.InputObjectType):
    eq = Date(description=FilterInputDescriptions.EQ, required=False)
    one_of = NonNullList(
        Date, description=FilterInputDescriptions.ONE_OF, required=False
    )
    range = DateRangeInput(description=FilterInputDescriptions.RANGE, required=False)

    class Meta:
        description = (
            "Define the filtering options for date fields."
            + ADDED_IN_311
            + PREVIEW_FEATURE
        )


class DateTimeFilterInput(graphene.InputObjectType):
    eq = graphene.DateTime(description=FilterInputDescriptions.EQ, required=False)
    one_of = NonNullList(
        graphene.DateTime,
        description=FilterInputDescriptions.ONE_OF,
        required=False,
    )
    range = DateTimeRangeInput(
        description=FilterInputDescriptions.RANGE, required=False
    )

    class Meta:
        description = (
            "Define the filtering options for date time fields."
            + ADDED_IN_311
            + PREVIEW_FEATURE
        )

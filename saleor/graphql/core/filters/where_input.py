import graphene

from ..scalars import UUID, Date, DateTime, Decimal
from ..types import NonNullList
from ..types.common import (
    DateRangeInput,
    DateTimeRangeInput,
    DecimalRangeInput,
    IntRangeInput,
)
from .filter_input import FilterInputObjectType


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
    def __init_subclass_with_meta__(cls, _meta=None, **options):  # type: ignore[override]
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
    NOT_ONE_OF = "The value not included in."
    RANGE = "The value in range."


class StringFilterInput(graphene.InputObjectType):
    eq = graphene.String(description=FilterInputDescriptions.EQ, required=False)
    one_of = NonNullList(
        graphene.String,
        description=FilterInputDescriptions.ONE_OF,
        required=False,
    )

    class Meta:
        description = "Define the filtering options for string fields."


class IntFilterInput(graphene.InputObjectType):
    eq = graphene.Int(description=FilterInputDescriptions.EQ, required=False)
    one_of = NonNullList(
        graphene.Int, description=FilterInputDescriptions.ONE_OF, required=False
    )
    range = IntRangeInput(description=FilterInputDescriptions.RANGE, required=False)

    class Meta:
        description = "Define the filtering options for integer fields."


class DecimalFilterInput(graphene.InputObjectType):
    eq = Decimal(description=FilterInputDescriptions.EQ, required=False)
    one_of = NonNullList(
        Decimal, description=FilterInputDescriptions.ONE_OF, required=False
    )
    range = DecimalRangeInput(description=FilterInputDescriptions.RANGE, required=False)

    class Meta:
        description = "Define the filtering options for decimal fields."


class DateFilterInput(graphene.InputObjectType):
    eq = Date(description=FilterInputDescriptions.EQ, required=False)
    one_of = NonNullList(
        Date, description=FilterInputDescriptions.ONE_OF, required=False
    )
    range = DateRangeInput(description=FilterInputDescriptions.RANGE, required=False)

    class Meta:
        description = "Define the filtering options for date fields."


class DateTimeFilterInput(graphene.InputObjectType):
    eq = DateTime(description=FilterInputDescriptions.EQ, required=False)
    one_of = NonNullList(
        DateTime,
        description=FilterInputDescriptions.ONE_OF,
        required=False,
    )
    range = DateTimeRangeInput(
        description=FilterInputDescriptions.RANGE, required=False
    )

    class Meta:
        description = "Define the filtering options for date time fields."


class GlobalIDFilterInput(graphene.InputObjectType):
    eq = graphene.ID(description=FilterInputDescriptions.EQ, required=False)
    one_of = NonNullList(
        graphene.ID,
        description=FilterInputDescriptions.ONE_OF,
        required=False,
    )

    class Meta:
        description = "Define the filtering options for foreign key fields."


class UUIDFilterInput(graphene.InputObjectType):
    eq = UUID(description=FilterInputDescriptions.EQ, required=False)
    one_of = NonNullList(
        UUID,
        description=FilterInputDescriptions.ONE_OF,
        required=False,
    )

    class Meta:
        description = "Define the filtering options for string fields."


class PriceFilterInput(graphene.InputObjectType):
    currency = graphene.String(
        required=False, description="The currency of the price to filter by."
    )
    amount = DecimalFilterInput(
        required=True, description="The amount of the price to filter by."
    )


class MetadataValueFilterInput(graphene.InputObjectType):
    eq = graphene.String(description=FilterInputDescriptions.EQ, required=False)
    one_of = NonNullList(
        graphene.String, description=FilterInputDescriptions.ONE_OF, required=False
    )

    class Meta:
        description = "Define the filtering options for metadata value fields."


class MetadataFilterInput(graphene.InputObjectType):
    key = graphene.String(
        required=True,
        description="Key to filter by. If not other fields provided - checking the existence of the key in metadata.",
    )
    value = MetadataValueFilterInput(
        required=False,
        description="Value to filter by.",
    )

    class Meta:
        description = """Allows filtering based on metadata key/value pairs.

        Examples:
        - `{key: "size"}`
          Matches objects where the metadata key "size" exists, regardless of its value.
        - `{key: "color", value: {oneOf: ["blue", "green"]}}`
          Matches objects where the metadata key "color" is set to either "blue" or "green".
        - `{key: "status", value: {eq: "active"}}`
          Matches objects where the metadata key "status" is set to "active".
        """

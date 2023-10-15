import copy

import graphene
from graphene.types.inputobjecttype import InputObjectTypeOptions

from ..descriptions import DEPRECATED_IN_3X_INPUT
from ..enums import OrderDirection
from .base import BaseInputObjectType


class SortInputMeta(InputObjectTypeOptions):
    sort_enum = None


class SortInputObjectType(BaseInputObjectType):
    direction = graphene.Argument(
        OrderDirection,
        required=True,
        description="Specifies the direction in which to sort.",
    )

    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
        cls, container=None, _meta=None, sort_enum=None, type_name=None, **options
    ):
        if not _meta:
            _meta = SortInputMeta(cls)
        if sort_enum:
            _meta.sort_enum = sort_enum

        super().__init_subclass_with_meta__(container, _meta, **options)
        if type_name:
            field = copy.copy(cls._meta.fields["direction"])
            field.description = f"Specifies the direction in which to sort {type_name}."
            cls._meta.fields["direction"] = field
            if sort_enum and "field" not in cls._meta.fields:
                field = graphene.Argument(
                    sort_enum,
                    required=True,
                    description=f"Sort {type_name} by the selected field.",
                )
                cls._meta.fields.update({"field": field})


class ChannelSortInputObjectType(SortInputObjectType):
    channel = graphene.Argument(
        graphene.String,
        description=(
            "Specifies the channel in which to sort the data."
            f"{DEPRECATED_IN_3X_INPUT} Use root-level channel argument instead."
        ),
    )

    class Meta:
        abstract = True

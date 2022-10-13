import graphene
from graphene.types.objecttype import ObjectTypeOptions

from ..descriptions import DEPRECATED_IN_3X_INPUT
from ..enums import OrderDirection


class SortInputMeta(ObjectTypeOptions):
    sort_enum = None


class SortInputObjectType(graphene.InputObjectType):
    direction = graphene.Argument(
        OrderDirection,
        required=True,
        description="Specifies the direction in which to sort products.",
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
        if sort_enum and type_name:
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

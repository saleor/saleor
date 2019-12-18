import graphene

from ..enums import OrderDirection


class SortInputObjectType(graphene.InputObjectType):
    direction = graphene.Argument(
        OrderDirection,
        required=True,
        description="Specifies the direction in which to sort products.",
    )

    @classmethod
    def __init_subclass_with_meta__(
        cls, container=None, _meta=None, sort_enum=None, type_name=None, **options
    ):
        super().__init_subclass_with_meta__(container, _meta, **options)
        if sort_enum and type_name:
            field = graphene.Argument(
                sort_enum,
                required=True,
                description=f"Sort {type_name} by the selected field.",
            )
            cls._meta.fields.update({"field": field})

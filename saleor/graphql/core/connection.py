from typing import Union

import graphene
import opentracing as ot
from django.db.models import Manager, QuerySet
from graphene import Field, List, NonNull, ObjectType, String
from graphene.relay.connection import Connection
from graphene_django_optimizer.types import OptimizedDjangoObjectType


class NonNullConnection(Connection):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, node=None, name=None, **options):
        super().__init_subclass_with_meta__(node=node, name=name, **options)

        # Override the original EdgeBase type to make to `node` field required.
        class EdgeBase:
            node = Field(
                cls._meta.node,
                description="The item at the end of the edge.",
                required=True,
            )
            cursor = String(
                required=True, description="A cursor for use in pagination."
            )

        # Create the edge type using the new EdgeBase.
        edge_name = cls.Edge._meta.name
        edge_bases = (EdgeBase, ObjectType)
        edge = type(edge_name, edge_bases, {})
        cls.Edge = edge

        # Override the `edges` field to make it non-null list
        # of non-null edges.
        cls._meta.fields["edges"] = Field(NonNull(List(NonNull(cls.Edge))))


class CountableConnection(NonNullConnection):
    class Meta:
        abstract = True

    total_count = graphene.Int(description="A total count of items in the collection.")

    @staticmethod
    def resolve_total_count(root, *_args, **_kwargs):
        return root.length


class CountableDjangoObjectType(OptimizedDjangoObjectType):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, *args, **kwargs):
        # Force it to use the countable connection
        countable_conn = CountableConnection.create_type(
            "{}CountableConnection".format(cls.__name__), node=cls
        )
        super().__init_subclass_with_meta__(*args, connection=countable_conn, **kwargs)

    @classmethod
    def maybe_optimize(cls, info, qs: Union[QuerySet, Manager], pk):
        with ot.global_tracer().start_active_span("optimizer") as scope:
            span = scope.span
            span.set_tag("optimizer.pk", pk)
            span.set_tag("optimizer.model", cls._meta.model.__name__)
            return super().maybe_optimize(info, qs, pk)

    @classmethod
    def get_node(cls, info, id):
        with ot.global_tracer().start_active_span("node") as scope:
            span = scope.span
            span.set_tag("node.pk", id)
            span.set_tag("node.type", cls.__name__)
            return super().get_node(info, id)

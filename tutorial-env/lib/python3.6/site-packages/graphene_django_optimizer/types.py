from graphene.types.definitions import GrapheneObjectType
from graphene_django.types import DjangoObjectType

from .query import query


class OptimizedDjangoObjectType(DjangoObjectType):
    class Meta:
        abstract = True

    @classmethod
    def can_optimize_resolver(cls, resolver_info):
        return (
            isinstance(resolver_info.return_type, GrapheneObjectType)
            and resolver_info.return_type.graphene_type is cls)

    @classmethod
    def get_optimized_node(cls, info, qs, pk):
        return query(qs, info).get(pk=pk)

    @classmethod
    def maybe_optimize(cls, info, qs, pk):
        try:
            if cls.can_optimize_resolver(info):
                return cls.get_optimized_node(info, qs, pk)
            return qs.get(pk=pk)
        except cls._meta.model.DoesNotExist:
            return None

    @classmethod
    def get_node(cls, info, id):
        """
        Bear in mind that if you are overriding this method get_node(info, pk),
        you should always call maybe_optimize(info, qs, pk)
        and never directly call get_optimized_node(info, qs, pk) as it would
        result to the node being attempted to be optimized when it is not
        supposed to actually get optimized.

        :param info:
        :param id:
        :return:
        """
        return cls.maybe_optimize(info, cls._meta.model.objects, id)

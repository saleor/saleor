import graphene

from . import mixins


class Revoke(mixins.RevokeMixin, graphene.Mutation):

    class Arguments:
        refresh_token = graphene.String(required=True)

    @classmethod
    def mutate(cls, *args, **kwargs):
        return cls.revoke(*args, **kwargs)

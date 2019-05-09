import graphene

from . import mixins


class Revoke(mixins.RevokeMixin, graphene.ClientIDMutation):

    class Input:
        refresh_token = graphene.String(required=True)

    @classmethod
    def mutate_and_get_payload(cls, *args, **kwargs):
        return cls.revoke(*args, **kwargs)

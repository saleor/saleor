import graphene

from .mutations import ChannelCreate


class ChannelMutations(graphene.ObjectType):
    channel_create = ChannelCreate.Field()

import graphene

from ...channel import models
from ...core.tracing import traced_resolver
from .types import Channel


@traced_resolver
def resolve_channel(info, id):
    return graphene.Node.get_node_from_global_id(info, id, Channel)


def resolve_channels():
    return models.Channel.objects.all()

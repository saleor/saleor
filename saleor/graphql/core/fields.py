import json
from functools import partial

import graphe
from graphene.relay import PageInfo
from graphene_django.fields import DjangoConnectionField
from graphql.error import GraphQLError
from graphql.language.ast import FragmentSpread
from graphql_relay.connection.arrayconnection import connection_from_list_slice
from promise import Promise

from ...channel.exceptions import ChannelNotDefined, NoDefaultChannel
from ..channel import ChannelContext, ChannelQsContext
from ..channel.utils import get_default_channel_slug_or_graphql_error
from ..utils.sorting import sort_queryset_for_connection
from .connection import connection_from_queryset_slice


def patch_pagination_args(field: DjangoConnectionField):
    """Add descriptions to pagination arguments in a connection field.

    By default Graphene's connection fields comes without description for pagination
    arguments. This functions patches those fields to add the descriptions.
    """
    field.args["first"].description = "Return the first n elements from the list."
    field.args["last"].description = "Return the last n elements from the list."
    field.args[
        "before"
    ].description = (
        "Return the elements in the list that come before the specified cursor."
    )
    field.args[
        "after"
    ].description = (
        "Return the elements in the list that come after the specified cursor."
    )


class BaseConnectionField(graphene.ConnectionField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        patch_pagination_args(self)

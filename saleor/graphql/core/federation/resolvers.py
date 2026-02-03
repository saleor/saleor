from typing import Any

import graphene
from django.core.exceptions import ValidationError
from graphql.error import GraphQLError

from ..utils import from_global_id_or_error


def resolve_id_or_error(idx: Any, graphql_type: type[graphene.ObjectType] | str):
    # Note: 'graphene.GlobalID' type happens when a user provides other fields
    #       (e.g., 'userEmail') but doesn't provide a value for 'id'.
    #       This is likely Graphene putting a placeholder until the field is resolved.
    if not idx or isinstance(idx, graphene.GlobalID):
        raise GraphQLError("Missing required field: id")
    if isinstance(idx, str) is False:
        raise GraphQLError("ID must be a string")

    try:
        _object_type, resolved_id = from_global_id_or_error(
            idx,
            only_type=graphql_type,
            raise_error=True,
        )
    except ValidationError as exc:
        raise GraphQLError(str(exc)) from exc
    return resolved_id


def resolve_federation_references(
    graphql_type: type[graphene.ObjectType] | str, roots, queryset
):
    ids = [resolve_id_or_error(root.id, graphql_type) for root in roots]
    objects = {str(obj.id): obj for obj in queryset.filter(id__in=ids)}
    return [objects.get(root_id) for root_id in ids]

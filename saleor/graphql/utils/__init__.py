from typing import TYPE_CHECKING, Optional, Union

import graphene
from django.conf import settings
from django.db.models import Value
from django.db.models.functions import Concat
from graphene_django.registry import get_global_registry
from graphql.error import GraphQLError
from graphql_relay import from_global_id

from ...account import models as account_models
from ..core.enums import PermissionEnum
from ..core.types import Permission

if TYPE_CHECKING:
    from ..account import types as account_types


ERROR_COULD_NO_RESOLVE_GLOBAL_ID = (
    "Could not resolve to a node with the global id list of '%s'."
)
registry = get_global_registry()
REVERSED_DIRECTION = {
    "-": "",
    "": "-",
}


def resolve_global_ids_to_primary_keys(
    ids, graphene_type=None, raise_error: bool = False
):
    pks = []
    invalid_ids = []
    used_type = graphene_type

    for graphql_id in ids:
        if not graphql_id:
            invalid_ids.append(graphql_id)
            continue

        try:
            node_type, _id = from_global_id(graphql_id)
        except Exception:
            invalid_ids.append(graphql_id)
            continue

        # Raise GraphQL error if ID of a different type was passed
        if used_type and str(used_type) != str(node_type):
            if not raise_error:
                continue
            raise GraphQLError(f"Must receive {str(used_type)} id: {graphql_id}.")

        used_type = node_type
        pks.append(_id)

    if invalid_ids:
        raise GraphQLError(ERROR_COULD_NO_RESOLVE_GLOBAL_ID % invalid_ids)

    return used_type, pks


def _resolve_graphene_type(type_name):
    for _, _type in registry._registry.items():
        if _type._meta.name == type_name:
            return _type
    raise GraphQLError("Could not resolve the type {}".format(type_name))


def get_nodes(
    ids, graphene_type: Union[graphene.ObjectType, str] = None, model=None, qs=None
):
    """Return a list of nodes.

    If the `graphene_type` argument is provided, the IDs will be validated
    against this type. If the type was not provided, it will be looked up in
    the Graphene's registry. Raises an error if not all IDs are of the same
    type.

    If the `graphene_type` is of type str, the model keyword argument must be provided.
    """
    nodes_type, pks = resolve_global_ids_to_primary_keys(
        ids, graphene_type, raise_error=True
    )

    # If `graphene_type` was not provided, check if all resolved types are
    # the same. This prevents from accidentally mismatching IDs of different
    # types.
    if nodes_type and not graphene_type:
        graphene_type = _resolve_graphene_type(nodes_type)

    if qs is None and graphene_type and not isinstance(graphene_type, str):
        qs = graphene_type._meta.model.objects
    elif model is not None:
        qs = model.objects

    nodes = list(qs.filter(pk__in=pks))
    nodes.sort(key=lambda e: pks.index(str(e.pk)))  # preserve order in pks

    if not nodes:
        raise GraphQLError(ERROR_COULD_NO_RESOLVE_GLOBAL_ID % ids)

    nodes_pk_list = [str(node.pk) for node in nodes]
    for pk in pks:
        assert pk in nodes_pk_list, "There is no node of type {} with pk {}".format(
            graphene_type, pk
        )
    return nodes


def format_permissions_for_display(permissions):
    """Transform permissions queryset into Permission list.

    Keyword Arguments:
        permissions - queryset with permissions

    """
    permissions_data = permissions.annotate(
        formated_codename=Concat("content_type__app_label", Value("."), "codename")
    ).values("name", "formated_codename")

    formatted_permissions = [
        Permission(
            code=PermissionEnum.get(data["formated_codename"]), name=data["name"]
        )
        for data in permissions_data
    ]
    return formatted_permissions


def get_user_or_app_from_context(context):
    # order is important
    # app can be None but user if None then is passed as anonymous
    return context.app or context.user


def requestor_is_superuser(requestor):
    """Return True if requestor is superuser."""
    return getattr(requestor, "is_superuser", False)


def get_user_country_context(
    destination_address: Optional[
        Union["account_types.AddressInput", "account_models.Address"]
    ] = None,
    company_address: Optional["account_models.Address"] = None,
) -> str:
    """Get country of the current user to use for tax and stock related calculations.

    User's country context is determined from the provided `destination_address` (which
    may represent user's current location determined by the client or a shipping
    address provided in the checkout). If `destination_address` is not given, the
    default company address from the shop settings is assumed. If this address is not
    set, fallback to the `DEFAULT_COUNTRY` setting.
    """
    if destination_address and destination_address.country:
        if isinstance(destination_address, account_models.Address):
            return destination_address.country.code
        return destination_address.country
    elif company_address and company_address.country:
        return company_address.country.code
    return settings.DEFAULT_COUNTRY

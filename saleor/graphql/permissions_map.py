from typing import TYPE_CHECKING, Any, List, Optional, Union

import graphql
from graphql.execution.base import (
    ExecutionContext,
    ResolveInfo,
    default_resolve_fn,
    get_field_def,
)
from graphql.execution.executor import complete_value_catching_error, resolve_or_error
from graphql.utils.undefined import Undefined

from ..core.exceptions import PermissionDenied
from ..core.permissions import AccountPermissions, OrderPermissions
from .decorators import (
    account_passes_test,
    one_of_permissions_required,
    permission_required,
)

if TYPE_CHECKING:
    from graphql.language.ast import Field
    from graphql.type.definition import GraphQLObjectType

# TODO
# - cleaner way to inject the permission map logic to executor
# - pass data objects to permission functions


def is_authenticated():
    def _check_is_authenticated(context):
        print("Check is authenticated")
        user = context.user
        if not user or not user.is_authenticated:
            raise PermissionDenied(
                message="You need to be authenticated to access this field"
            )

    return account_passes_test(_check_is_authenticated)


has_perms = permission_required
has_one_of_perms = one_of_permissions_required


PERMISSIONS_MAP = {
    # "Mutation": {
    #     "accountAddressUpdate": has_perms(AccountPermissions.MANAGE_USERS)
    #     or (is_authenticated() and is_address_owner)
    # },
    "Query": {
        "customers": has_one_of_perms(
            [OrderPermissions.MANAGE_ORDERS, AccountPermissions.MANAGE_USERS]
        ),
        "permissionGroups": has_perms(AccountPermissions.MANAGE_STAFF),
        "permissionGroup": has_perms(AccountPermissions.MANAGE_STAFF),
        "staffUsers": has_perms(AccountPermissions.MANAGE_STAFF),
        "user": has_one_of_perms(
            [
                AccountPermissions.MANAGE_STAFF,
                AccountPermissions.MANAGE_USERS,
                OrderPermissions.MANAGE_ORDERS,
            ]
        ),
    },
}


def resolve_field_with_permissions_map(
    exe_context,  # type: ExecutionContext
    parent_type,  # type: GraphQLObjectType
    source,  # type: Any
    field_asts,  # type: List[Field]
    parent_info,  # type: Optional[ResolveInfo]
    field_path,  # type: List[Union[int, str]]
):
    field_ast = field_asts[0]
    field_name = field_ast.name.value

    field_def = get_field_def(exe_context.schema, parent_type, field_name)
    if not field_def:
        return Undefined

    return_type = field_def.type
    resolve_fn = field_def.resolver or default_resolve_fn

    # EXPERIMENTAL: use permission map
    permissions_map = getattr(exe_context.context_value, "_permissions_map")
    if permissions_map:
        permission_fn = permissions_map.get(parent_type.name, {}).get(field_name)
        print("PermissionFn: ", parent_type.name, field_name, permission_fn)
        if permission_fn:
            resolve_fn = permission_fn(resolve_fn)

    # We wrap the resolve_fn from the middleware
    resolve_fn_middleware = exe_context.get_field_resolver(resolve_fn)

    # Build a dict of arguments from the field.arguments AST, using the variables scope
    #  to fulfill any variable references.
    args = exe_context.get_argument_values(field_def, field_ast)

    # The resolve function's optional third argument is a context value that
    # is provided to every resolve function within an execution. It is commonly
    # used to represent an authenticated user, or request-specific caches.
    context = exe_context.context_value

    # The resolve function's optional third argument is a collection of
    # information about the current execution state.
    info = ResolveInfo(
        field_name,
        field_asts,
        return_type,
        parent_type,
        schema=exe_context.schema,
        fragments=exe_context.fragments,
        root_value=exe_context.root_value,
        operation=exe_context.operation,
        variable_values=exe_context.variable_values,
        context=context,
        path=field_path,
    )

    executor = exe_context.executor
    result = resolve_or_error(resolve_fn_middleware, source, info, args, executor)

    return complete_value_catching_error(
        exe_context, return_type, field_asts, info, field_path, result
    )


# TODO: Find a cleaner way to inject permission map logic to graphql-core
graphql.execution.executor.resolve_field = resolve_field_with_permissions_map

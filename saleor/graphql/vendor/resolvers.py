# @traced_resolver
# def resolve_address(info, id, app):
#     user = info.context.user
#     _, address_pk = from_global_id_or_error(id, Address)
#     if app and app.has_perm(AccountPermissions.MANAGE_USERS):
#         return (
#             models.Address.objects.using(get_database_connection_name(info.context))
#             .filter(pk=address_pk)
#             .first()
#         )
#     if user:
#         return user.addresses.filter(id=address_pk).first()
#     raise PermissionDenied(
#         permissions=[AccountPermissions.MANAGE_USERS, AuthorizationFilters.OWNER]
#     )

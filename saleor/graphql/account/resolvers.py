from graphql_jwt.decorators import login_required

from ...account import models
from ..utils import get_node
from .types import User


@login_required
def resolve_users(info):
    user = info.context.user
    if user.get_all_permissions() & {'account.view_user', 'account.edit_user'}:
        qs =  models.User.objects.all().prefetch_related('addresses')
        return qs
    # FIXME: Returning 'None' makes graphene return all users
    return models.User.objects.none()


@login_required
def resolve_user(info, id):
    user = get_node(info, id, only_type=User)
    requesting_user = info.context.user
    if (user == requesting_user or requesting_user.get_all_permissions() & {
            'account.view_user', 'account.edit_user'}):
        return user
    return None

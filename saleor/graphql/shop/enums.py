import graphene

from ..core.utils import str_to_enum
from ...site import AuthenticationBackends


AuthorizationKeyType = graphene.Enum(
    'AuthorizationKeyType', [(str_to_enum(auth_type[0]), auth_type[0])
                             for auth_type in AuthenticationBackends.BACKENDS])

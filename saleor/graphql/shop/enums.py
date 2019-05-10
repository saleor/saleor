import graphene

from ...site import AuthenticationBackends
from ..core.utils import str_to_enum

AuthorizationKeyType = graphene.Enum(
    "AuthorizationKeyType",
    [
        (str_to_enum(auth_type[0]), auth_type[0])
        for auth_type in AuthenticationBackends.BACKENDS
    ],
)

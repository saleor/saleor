import graphene

from ....account import models as account_models
from ....app import models as app_models
from ...account import types as account_types
from ...app import types as app_types


# The file hasn't been attached to the __init__ file as it generates the circular
# graphql import. Graphene for Union types requires already initialized types so
# we need to provide a fully initialized type.
class UserOrApp(graphene.Union):
    class Meta:
        types = (account_types.User, app_types.App)

    @classmethod
    def resolve_type(cls, instance, info):
        # Support restricted user for AppProblem permission checks
        if hasattr(instance, "_is_restricted_user"):
            return account_types.User
        if isinstance(instance, account_models.User):
            return account_types.User
        if isinstance(instance, app_models.App):
            return app_types.App
        return super().resolve_type(instance, info)

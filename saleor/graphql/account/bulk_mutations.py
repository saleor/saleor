import graphene

from ...account import models
from ..core.mutations import ModelBulkDeleteMutation
from .utils import CustomerDeleteMixin, StaffDeleteMixin


class UserBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of sale IDs to delete."
        )

    class Meta:
        abstract = True


class CustomerBulkDelete(CustomerDeleteMixin, UserBulkDelete):
    class Meta:
        description = "Deletes customers."
        model = models.User

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm("account.manage_users")


class StaffBulkDelete(StaffDeleteMixin, UserBulkDelete):
    class Meta:
        description = "Deletes staff users."
        model = models.User

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm("account.manage_staff")

import graphene

from ...account import models
from ..core.mutations import ModelBulkDeleteMutation


class UserBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description='List of sale IDs to delete.')

    class Meta:
        abstract = True

    @classmethod
    def clean_instance(cls, info, instance, errors):
        user = info.context.user
        if instance == user:
            cls.add_error(
                errors, 'id', 'You cannot delete your own account.')
        elif instance.is_superuser:
            cls.add_error(
                errors, 'id', 'Only superuser can delete his own account.')


class CustomerBulkDelete(UserBulkDelete):
    class Meta:
        description = 'Deletes customers.'
        model = models.User

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('account.manage_users')

    @classmethod
    def clean_instance(cls, info, instance, errors):
        super().clean_instance(info, instance, errors)
        if instance.is_staff:
            cls.add_error(errors, 'id', 'Cannot delete a staff account.')


class StaffBulkDelete(ModelBulkDeleteMutation):
    class Meta:
        description = 'Deletes staff users.'
        model = models.User

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('account.manage_staff')

    @classmethod
    def clean_instance(cls, info, instance, errors):
        super().clean_instance(info, instance, errors)
        if not instance.is_staff:
            cls.add_error(
                errors, 'id', 'Cannot delete a non-staff user.')

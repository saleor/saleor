from django.core.exceptions import ValidationError
import graphene

from ...account import models
from ..core.mutations import BaseBulkMutation, ModelBulkDeleteMutation
from .utils import CustomerDeleteMixin, StaffDeleteMixin


class UserBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description='List of sale IDs to delete.')

    class Meta:
        abstract = True


class CustomerBulkDelete(CustomerDeleteMixin, UserBulkDelete):
    class Meta:
        description = 'Deletes customers.'
        model = models.User
        permissions = ('account.manage_users', )


class StaffBulkDelete(StaffDeleteMixin, UserBulkDelete):
    class Meta:
        description = 'Deletes staff users.'
        model = models.User
        permissions = ('account.manage_staff', )


class UserBulkSetActive(BaseBulkMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description='List of user IDs to (de)activate).')
        is_active = graphene.Boolean(
            required=True,
            description='Determine if users will be set active or not.')

    class Meta:
        description = 'Activate or deactivate users.'
        model = models.User
        permissions = ('account.manage_users', )

    @classmethod
    def clean_instance(cls, info, instance):
        if info.context.user == instance:
            raise ValidationError({
                'is_active':
                    'Cannot activate or deactivate your own account.'})
        elif instance.is_superuser:
            raise ValidationError({
                'is_active':
                    'Cannot activate or deactivate superuser\'s account.'})

    @classmethod
    def bulk_action(cls, queryset, is_active):
        queryset.update(is_active=is_active)

import graphene

from ...account import models
from ...core.permissions import get_permissions, MODELS_PERMISSIONS
from ..core.mutations import ModelMutation


class UserInput(graphene.InputObjectType):
    email = graphene.String(
        description='The unique email address of the user.')
    note = graphene.String(description='A note about the user.')
    # FIXME: decide what to do with is_active field.


class StaffInput(UserInput):
    permissions = graphene.List(
        graphene.String,
        description='List of permission code names to assign to this user.')
    groups = graphene.List(
        graphene.ID,
        description='List of IDs of permission groups to assign the user to.')


class CustomerCreate(ModelMutation):
    class Arguments:
        input = UserInput()

    class Meta:
        description = 'Creates a new customer.'
        exclude = ['password']
        model = models.User

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('account.edit_user')


class CustomerUpdate(CustomerCreate):
    class Arguments:
        id = graphene.ID()
        input = UserInput()

    class Meta:
        description = 'Updates an existing customer.'
        exclude = ['password']
        model = models.User


class StaffCreate(ModelMutation):
    class Arguments:
        input = StaffInput()

    class Meta:
        description = 'Creates a new staff user.'
        exclude = ['password']
        model = models.User

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.is_staff

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        cleaned_input = super().clean_input(info, instance, input, errors)

        if 'permissions' in cleaned_input:
            permissions = cleaned_input['permissions']
            cleaned_permissions = []
            for code in permissions:
                if code not in MODELS_PERMISSIONS:
                    error_msg = 'Unknown permission: %s' % code
                    cls.add_error(errors, 'permissions', error_msg)
                else:
                    cleaned_permissions.append(code)
            if not errors:
                permission_objs = get_permissions(cleaned_permissions)
                cleaned_input['user_permissions'] = permission_objs
        return cleaned_input


class StaffUpdate(StaffCreate):
    class Arguments:
        id = graphene.ID()
        input = StaffInput()

    class Meta:
        description = 'Updates an existing staff user.'
        exclude = ['password']
        model = models.User


class SetPasswordInput(graphene.InputObjectType):
    token = graphene.String(
        description='A one-time token required to set the password.')
    password = graphene.String(description='Password')


class SetPassword(ModelMutation):
    class Arguments:
        id = graphene.ID()
        input = SetPasswordInput()

    class Meta:
        description = 'Sets user password.'
        model = models.User

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        cleaned_input = super().clean_input(info, instance, input, errors)
        cleaned_input.pop('token')
        return cleaned_input

    # FIXME: make sure about the permissions. At the moment any user with
    # valid token can set the password.

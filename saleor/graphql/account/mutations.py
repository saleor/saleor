import graphene
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from graphql_jwt.decorators import permission_required
from graphql_jwt.exceptions import PermissionDenied

from ...account import emails, models
from ...core.permissions import MODELS_PERMISSIONS, get_permissions
from ...dashboard.staff.utils import remove_staff_member
from ..account.i18n import I18nMixin
from ..account.types import AddressInput, User
from ..core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ..core.types.common import Error


def send_user_password_reset_email(user, site):
    context = {
        'email': user.email,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
        'token': default_token_generator.make_token(user),
        'site_name': site.name,
        'domain': site.domain,
        'protocol': 'https' if settings.ENABLE_SSL else 'http'}
    emails.send_password_reset_email.delay(context, user.email)


BILLING_ADDRESS_FIELD = 'default_billing_address'
SHIPPING_ADDRESS_FIELD = 'default_shipping_address'


class CustomerRegisterInput(graphene.InputObjectType):
    email = graphene.String(
        description='The unique email address of the user.', required=True)
    password = graphene.String(description='Password', required=True)


class CustomerRegister(ModelMutation):
    class Arguments:
        input = CustomerRegisterInput(
            description='Fields required to create a user.', required=True)

    class Meta:
        description = 'Register a new user.'
        exclude = ['password']
        model = models.User

    @classmethod
    def save(cls, info, user, cleaned_input):
        password = cleaned_input['password']
        user.set_password(password)
        user.save()


class UserInput(graphene.InputObjectType):
    email = graphene.String(
        description='The unique email address of the user.')
    is_active = graphene.Boolean(
        required=False, description='User account is active.')
    note = graphene.String(description='A note about the user.')


class UserAddressInput(graphene.InputObjectType):
    default_billing_address = AddressInput(
        description='Billing address of the customer.')
    default_shipping_address = AddressInput(
        description='Shipping address of the customer.')


class CustomerInput(UserInput, UserAddressInput):
    pass


class UserCreateInput(CustomerInput):
    send_password_email = graphene.Boolean(
        description='Send an email with a link to set a password')


class StaffInput(UserInput):
    permissions = graphene.List(
        graphene.String,
        description='List of permission code names to assign to this user.')


class StaffCreateInput(StaffInput):
    send_password_email = graphene.Boolean(
        description='Send an email with a link to set a password')


class CustomerCreate(ModelMutation, I18nMixin):
    class Arguments:
        input = UserCreateInput(
            description='Fields required to create a customer.', required=True)

    class Meta:
        description = 'Creates a new customer.'
        exclude = ['password']
        model = models.User

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('account.manage_users')

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        shipping_address_data = input.pop(SHIPPING_ADDRESS_FIELD, None)
        billing_address_data = input.pop(BILLING_ADDRESS_FIELD, None)
        cleaned_input = super().clean_input(info, instance, input, errors)

        if shipping_address_data:
            shipping_address, errors = cls.validate_address(
                shipping_address_data, errors, SHIPPING_ADDRESS_FIELD,
                instance=getattr(instance, SHIPPING_ADDRESS_FIELD))
            cleaned_input[SHIPPING_ADDRESS_FIELD] = shipping_address

        if billing_address_data:
            billing_address, errors = cls.validate_address(
                billing_address_data, errors, BILLING_ADDRESS_FIELD,
                instance=getattr(instance, BILLING_ADDRESS_FIELD))
            cleaned_input[BILLING_ADDRESS_FIELD] = billing_address
        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        default_shipping_address = cleaned_input.get(SHIPPING_ADDRESS_FIELD)
        if default_shipping_address:
            default_shipping_address.save()
            instance.default_shipping_address = default_shipping_address
        default_billing_address = cleaned_input.get(BILLING_ADDRESS_FIELD)
        if default_billing_address:
            default_billing_address.save()
            instance.default_billing_address = default_billing_address

        if cleaned_input.get('send_password_email'):
            site = info.context.site
            send_user_password_reset_email(instance, site)
        super().save(info, instance, cleaned_input)


class CustomerUpdate(CustomerCreate):
    class Arguments:
        id = graphene.ID(
            description='ID of a customer to update.', required=True)
        input = CustomerInput(
            description='Fields required to update a customer.', required=True)

    class Meta:
        description = 'Updates an existing customer.'
        exclude = ['password']
        model = models.User


class LoggedCustomerUpdate(CustomerCreate):
    class Arguments:
        id = graphene.ID(
            description='ID of a customer to update.', required=True)
        input = UserAddressInput(
            description='Fields required to update logged in customer.',
            required=True)

    class Meta:
        description = 'Updates an existing logged in customer.'
        exclude = ['password']
        model = models.User

    @classmethod
    def user_is_allowed(cls, user, input):
        id = graphene.Node.to_global_id('User', user.id)
        return user.has_perm('account.manage_users') or id == input['id']


class UserDelete(ModelDeleteMutation):
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
        return errors


class CustomerDelete(UserDelete):
    class Meta:
        description = 'Deletes a customer.'
        model = models.User

    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a customer to delete.')

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('account.manage_users')

    @classmethod
    def clean_instance(cls, info, instance, errors):
        super().clean_instance(info, instance, errors)
        if instance.is_staff:
            cls.add_error(errors, 'id', 'Cannot delete a staff account.')
        return errors


class StaffCreate(ModelMutation):
    class Arguments:
        input = StaffCreateInput(
            description='Fields required to create a staff user.',
            required=True)

    class Meta:
        description = 'Creates a new staff user.'
        exclude = ['password']
        model = models.User

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('account.manage_staff')

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        cleaned_input = super().clean_input(info, instance, input, errors)

        # set is_staff to True to create a staff user
        cleaned_input['is_staff'] = True

        # clean and prepare permissions
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

    @classmethod
    def save(cls, info, user, cleaned_input):
        user.save()
        if cleaned_input.get('send_password_email'):
            site = info.context.site
            send_user_password_reset_email(user, site)


class StaffUpdate(StaffCreate):
    class Arguments:
        id = graphene.ID(
            description='ID of a staff user to update.', required=True)
        input = StaffInput(
            description='Fields required to update a staff user.',
            required=True)

    class Meta:
        description = 'Updates an existing staff user.'
        exclude = ['password']
        model = models.User

    @classmethod
    def clean_is_active(cls, is_active, instance, user, errors):
        if is_active is None:
            return errors

        if not is_active:
            if user == instance:
                cls.add_error(
                    errors, 'is_active', 'Cannot deactivate your own account.')
            elif instance.is_superuser:
                cls.add_error(
                    errors, 'is_active',
                    'Cannot deactivate superuser\'s account.')
        return errors

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        cleaned_input = super().clean_input(info, instance, input, errors)
        cls.clean_is_active(
            cleaned_input.get('is_active'), instance, info.context.user,
            errors)
        return cleaned_input


class StaffDelete(UserDelete):
    class Meta:
        description = 'Deletes a staff user.'
        model = models.User

    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a staff user to delete.')

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('account.manage_staff')

    @classmethod
    def clean_instance(cls, info, instance, errors):
        super().clean_instance(info, instance, errors)
        if not instance.is_staff:
            cls.add_error(
                errors, 'id', 'Cannot delete a non-staff user.')
        return errors

    @classmethod
    def mutate(cls, root, info, **data):
        if not cls.user_is_allowed(info.context.user, data):
            raise PermissionDenied()

        errors = []
        user_id = data.get('id')
        instance = cls.get_node_or_error(info, user_id, errors, 'id', User)
        if instance:
            cls.clean_instance(info, instance, errors)
        if errors:
            return cls(errors=errors)

        db_id = instance.id
        remove_staff_member(instance)
        # After the instance is deleted, set its ID to the original database's
        # ID so that the success response contains ID of the deleted object.
        instance.id = db_id
        return cls.success_response(instance)


class SetPasswordInput(graphene.InputObjectType):
    token = graphene.String(
        description='A one-time token required to set the password.',
        required=True)
    password = graphene.String(description='Password', required=True)


class SetPassword(ModelMutation):
    INVALID_TOKEN = 'Invalid or expired token.'

    class Arguments:
        id = graphene.ID(
            description='ID of a user to set password whom.', required=True)
        input = SetPasswordInput(
            description='Fields required to set password.', required=True)

    class Meta:
        description = 'Sets user password.'
        model = models.User

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        cleaned_input = super().clean_input(info, instance, input, errors)
        token = cleaned_input.pop('token')
        if not default_token_generator.check_token(instance, token):
            cls.add_error(errors, 'token', SetPassword.INVALID_TOKEN)
        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.set_password(cleaned_input['password'])
        instance.save()


class PasswordReset(BaseMutation):
    class Arguments:
        email = graphene.String(description='Email', required=True)

    class Meta:
        description = 'Sends password reset email'

    @classmethod
    @permission_required('account.manage_users')
    def mutate(cls, root, info, email):
        try:
            user = models.User.objects.get(email=email)
        except ObjectDoesNotExist:
            return cls(
                errors=[
                    Error(
                        field='email',
                        message='User with this email doesn\'t exist')])
        site = info.context.site
        send_user_password_reset_email(user, site)


class CustomerPasswordResetInput(graphene.InputObjectType):
    email = graphene.String(
        required=True, description=(
            'Email of the user that will be used for password recovery.'))


class CustomerPasswordReset(BaseMutation):
    class Arguments:
        input = CustomerPasswordResetInput(
            description='Fields required to reset customer\'s password',
            required=True)

    class Meta:
        description = 'Resets the customer\'s password.'

    @classmethod
    def mutate(cls, root, info, input):
        email = input['email']
        try:
            user = models.User.objects.get(email=email)
        except ObjectDoesNotExist:
            return
        site = info.context.site
        send_user_password_reset_email(user, site)


class AddressCreateInput(AddressInput):
    user_id = graphene.ID(
        description='ID of a user to create address for', required=True)


class AddressCreate(ModelMutation):
    class Arguments:
        input = AddressCreateInput(
            description='Fields required to create address', required=True)

    class Meta:
        description = 'Creates user address'
        model = models.Address

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        user_id = input.pop('user_id')
        user = cls.get_node_or_error(info, user_id, errors, 'user_id', User)
        cleaned_input = super().clean_input(info, instance, input, errors)
        cleaned_input['user'] = user
        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        super().save(info, instance, cleaned_input)
        user = cleaned_input.get('user')
        if user:
            instance.user_addresses.add(user)
            instance.save()

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('account.manage_users')


class AddressUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(
            description='ID of address to update', required=True)
        input = AddressInput(
            description='Fields required to update address', required=True)

    class Meta:
        description = 'Updates address'
        model = models.Address
        exclude = ['user_addresses']

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('account.manage_users')


class AddressDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of address to delete.')

    class Meta:
        description = 'Deletes an address'
        model = models.Address

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('account.manage_users')

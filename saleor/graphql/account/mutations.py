import graphene
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from graphql_jwt.decorators import staff_member_required
from graphql_jwt.exceptions import PermissionDenied

from ...account import emails, models, utils
from ...account.thumbnails import create_user_avatar_thumbnails
from ...account.utils import get_random_avatar
from ...checkout import AddressType
from ...core.permissions import get_permissions
from ...dashboard.emails import (
    send_set_password_customer_email, send_set_password_staff_email)
from ...dashboard.staff.utils import remove_staff_member
from ..account.enums import AddressTypeEnum
from ..account.i18n import I18nMixin
from ..account.types import Address, AddressInput, User
from ..core.enums import PermissionEnum
from ..core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ..core.types import Upload
from ..core.utils import validate_image_file
from .utils import CustomerDeleteMixin, StaffDeleteMixin, UserDeleteMixin

BILLING_ADDRESS_FIELD = 'default_billing_address'
SHIPPING_ADDRESS_FIELD = 'default_shipping_address'


def send_user_password_reset_email(user, site):
    context = {
        'email': user.email,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
        'site_name': site.name,
        'domain': site.domain,
        'protocol': 'https' if settings.ENABLE_SSL else 'http'}
    emails.send_password_reset_email.delay(context, user.email)


def can_edit_address(user, address):
    """Determine whether the user can edit the given address.

    This method assumes that an address can be edited by:
    - users with proper permission (staff)
    - customers who "own" the given address.
    """
    has_perm = user.has_perm('account.manage_users')
    belongs_to_user = address in user.addresses.all()
    return has_perm or belongs_to_user


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
    first_name = graphene.String(description='Given name.')
    last_name = graphene.String(description='Family name.')
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
        PermissionEnum,
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
        permissions = ('account.manage_users', )

    @classmethod
    def clean_input(cls, info, instance, data):
        shipping_address_data = data.pop(SHIPPING_ADDRESS_FIELD, None)
        billing_address_data = data.pop(BILLING_ADDRESS_FIELD, None)
        cleaned_input = super().clean_input(info, instance, data)

        if shipping_address_data:
            shipping_address = cls.validate_address(
                shipping_address_data,
                instance=getattr(instance, SHIPPING_ADDRESS_FIELD))
            cleaned_input[SHIPPING_ADDRESS_FIELD] = shipping_address

        if billing_address_data:
            billing_address = cls.validate_address(
                billing_address_data,
                instance=getattr(instance, BILLING_ADDRESS_FIELD))
            cleaned_input[BILLING_ADDRESS_FIELD] = billing_address
        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        # FIXME: save address in user.addresses as well
        default_shipping_address = cleaned_input.get(SHIPPING_ADDRESS_FIELD)
        if default_shipping_address:
            default_shipping_address.save()
            instance.default_shipping_address = default_shipping_address
        default_billing_address = cleaned_input.get(BILLING_ADDRESS_FIELD)
        if default_billing_address:
            default_billing_address.save()
            instance.default_billing_address = default_billing_address

        super().save(info, instance, cleaned_input)

        if cleaned_input.get('send_password_email'):
            send_set_password_customer_email.delay(instance.pk)


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


class LoggedUserUpdate(CustomerCreate):
    class Arguments:
        input = UserAddressInput(
            description='Fields required to update logged in user.',
            required=True)

    class Meta:
        description = 'Updates data of the logged in user.'
        exclude = ['password']
        model = models.User

    @classmethod
    def check_permissions(cls, user):
        return user.is_authenticated

    @classmethod
    def perform_mutation(cls, root, info, **data):
        user = info.context.user
        data['id'] = graphene.Node.to_global_id('User', user.id)
        return super().perform_mutation(root, info, **data)


class UserDelete(UserDeleteMixin, ModelDeleteMutation):
    class Meta:
        abstract = True


class CustomerDelete(CustomerDeleteMixin, UserDelete):
    class Meta:
        description = 'Deletes a customer.'
        model = models.User
        permissions = ('account.manage_users', )

    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a customer to delete.')


class StaffCreate(ModelMutation):
    class Arguments:
        input = StaffCreateInput(
            description='Fields required to create a staff user.',
            required=True)

    class Meta:
        description = 'Creates a new staff user.'
        exclude = ['password']
        model = models.User
        permissions = ('account.manage_staff', )

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)

        # set is_staff to True to create a staff user
        cleaned_input['is_staff'] = True

        # clean and prepare permissions
        if 'permissions' in cleaned_input:
            permissions = cleaned_input.pop('permissions')
            cleaned_input['user_permissions'] = get_permissions(permissions)
        return cleaned_input

    @classmethod
    def save(cls, info, user, cleaned_input):
        user.avatar = get_random_avatar()
        user.save()
        create_user_avatar_thumbnails.delay(user_id=user.pk)
        if cleaned_input.get('send_password_email'):
            send_set_password_staff_email.delay(user.pk)


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
        permissions = ('account.manage_staff', )

    @classmethod
    def clean_is_active(cls, is_active, instance, user):
        if not is_active:
            if user == instance:
                raise ValidationError({
                    'is_active': 'Cannot deactivate your own account.'})
            elif instance.is_superuser:
                raise ValidationError({
                    'is_active': 'Cannot deactivate superuser\'s account.'})

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        is_active = cleaned_input.get('is_active')
        if is_active is not None:
            cls.clean_is_active(is_active, instance, info.context.user)
        return cleaned_input


class StaffDelete(StaffDeleteMixin, UserDelete):
    class Meta:
        description = 'Deletes a staff user.'
        model = models.User
        permissions = ('account.manage_staff', )

    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a staff user to delete.')

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        if not cls.check_permissions(info.context.user):
            raise PermissionDenied()

        user_id = data.get('id')
        instance = cls.get_node_or_error(info, user_id, only_type=User)
        cls.clean_instance(info, instance)

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
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        token = cleaned_input.pop('token')
        if not default_token_generator.check_token(instance, token):
            raise ValidationError({'token': SetPassword.INVALID_TOKEN})
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
        permissions = ('account.manage_users', )

    @classmethod
    def perform_mutation(cls, _root, info, email):
        try:
            user = models.User.objects.get(email=email)
        except ObjectDoesNotExist:
            raise ValidationError({
                'email': 'User with this email doesn\'t exist'})
        site = info.context.site
        send_user_password_reset_email(user, site)
        return PasswordReset()


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
    def perform_mutation(cls, _root, info, **data):
        email = data.get('input')['email']
        try:
            user = models.User.objects.get(email=email)
        except ObjectDoesNotExist:
            raise ValidationError({
                'email': 'User with this email doesn\'t exist'})
        site = info.context.site
        send_user_password_reset_email(user, site)
        return CustomerPasswordReset()


class AddressCreate(ModelMutation):
    user = graphene.Field(
        User, description='A user instance for which the address was created.')

    class Arguments:
        user_id = graphene.ID(
            description='ID of a user to create address for', required=True)
        input = AddressInput(
            description='Fields required to create address', required=True)

    class Meta:
        description = 'Creates user address'
        model = models.Address
        permissions = ('account.manage_users', )

    @classmethod
    def perform_mutation(cls, root, info, **data):
        user_id = data['user_id']
        user = cls.get_node_or_error(
            info, user_id, field='user_id', only_type=User)
        response = super().perform_mutation(root, info, **data)
        if not response.errors:
            user.addresses.add(response.address)
            response.user = user
        return response


class AddressUpdate(ModelMutation):
    user = graphene.Field(
        User, description='A user instance for which the address was edited.')

    class Arguments:
        id = graphene.ID(
            description='ID of the address to update', required=True)
        input = AddressInput(
            description='Fields required to update address', required=True)

    class Meta:
        description = 'Updates an address'
        model = models.Address
        exclude = ['user_addresses']

    @classmethod
    def clean_input(cls, info, instance, data):
        # Method check_permissions cannot be used for permission check, because
        # it doesn't have the address instance.
        if not can_edit_address(info.context.user, instance):
            raise PermissionDenied()
        return super().clean_input(info, instance, data)

    @classmethod
    def perform_mutation(cls, root, info, **data):
        response = super().perform_mutation(root, info, **data)
        user = response.address.user_addresses.first()
        response.user = user
        return response


class AddressDelete(ModelDeleteMutation):
    user = graphene.Field(
        User, description='A user instance for which the address was deleted.')

    class Arguments:
        id = graphene.ID(
            required=True, description='ID of the address to delete.')

    class Meta:
        description = 'Deletes an address'
        model = models.Address

    @classmethod
    def clean_instance(cls, info, instance):
        # Method check_permissions cannot be used for permission check, because
        # it doesn't have the address instance.
        if not can_edit_address(info.context.user, instance):
            raise PermissionDenied()
        return super().clean_instance(info, instance)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        if not cls.check_permissions(info.context.user):
            raise PermissionDenied()

        node_id = data.get('id')
        instance = cls.get_node_or_error(info, node_id, Address)
        if instance:
            cls.clean_instance(info, instance)

        db_id = instance.id

        # Return the first user that the address is assigned to. There is M2M
        # relation between users and addresses, but in most cases address is
        # related to only one user.
        user = instance.user_addresses.first()

        instance.delete()
        instance.id = db_id

        response = cls.success_response(instance)

        # Refresh the user instance to clear the default addresses. If the
        # deleted address was used as default, it would stay cached in the
        # user instance and the invalid ID returned in the response might cause
        # an error.
        user.refresh_from_db()

        response.user = user
        return response


class AddressSetDefault(BaseMutation):
    user = graphene.Field(User, description='An updated user instance.')

    class Arguments:
        address_id = graphene.ID(
            required=True,
            description='ID of the address.')
        user_id = graphene.ID(
            required=True,
            description='ID of the user to change the address for.')
        type = AddressTypeEnum(
            required=True,
            description='The type of address.')

    class Meta:
        description = 'Sets a default address for the given user.'
        permissions = ('account.manage_users', )

    @classmethod
    def perform_mutation(cls, _root, info, address_id, user_id, **data):
        address = cls.get_node_or_error(
            info, address_id, field='address_id', only_type=Address)
        user = cls.get_node_or_error(
            info, user_id, field='user_id', only_type=User)

        if address not in user.addresses.all():
            raise ValidationError({
                'address_id': 'The address doesn\'t belong to that user.'})

        if data.get('type') == AddressTypeEnum.BILLING.value:
            address_type = AddressType.BILLING
        else:
            address_type = AddressType.SHIPPING

        utils.change_user_default_address(user, address, address_type)
        return cls(user=user)


# The same as AddressCreate, but for the currently authenticated user.
class CustomerAddressCreate(ModelMutation):
    class Arguments:
        input = AddressInput(
            description='Fields required to create address', required=True)
        type = AddressTypeEnum(required=False, description=(
            'A type of address. If provided, the new address will be '
            'automatically assigned as the customer\'s default address '
            'of that type.'))

    class Meta:
        description = 'Create a new address for the customer.'
        model = models.Address
        exclude = ['user_addresses']

    @classmethod
    def check_permissions(cls, user):
        return user.is_authenticated

    @classmethod
    def perform_mutation(cls, root, info, **data):
        success_response = super().perform_mutation(root, info, **data)
        address_type = data.get('type', None)
        if address_type:
            user = info.context.user
            instance = success_response.address
            utils.change_user_default_address(user, instance, address_type)
        return success_response

    @classmethod
    def save(cls, info, instance, cleaned_input):
        super().save(info, instance, cleaned_input)
        user = info.context.user
        instance.user_addresses.add(user)


# The same as SetDefaultAddress, but for the currently authenticated user.
class CustomerSetDefaultAddress(BaseMutation):
    user = graphene.Field(User, description='An updated user instance.')

    class Arguments:
        id = graphene.ID(
            required=True, description='ID of the address to set as default.')
        type = AddressTypeEnum(
            required=True, description='The type of address.')

    class Meta:
        description = 'Sets a default address for the authenticated user.'

    @classmethod
    def check_permissions(cls, user):
        return user.is_authenticated

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        address = cls.get_node_or_error(info, data.get('id'), Address)

        user = info.context.user
        if address not in user.addresses.all():
            raise ValidationError({
                'id': 'The address doesn\'t belong to that user.'})

        if data.get('type') == AddressTypeEnum.BILLING.value:
            address_type = AddressType.BILLING
        else:
            address_type = AddressType.SHIPPING

        utils.change_user_default_address(user, address, address_type)
        return cls(user=user)


class UserAvatarUpdate(BaseMutation):
    user = graphene.Field(User, description='An updated user instance.')

    class Arguments:
        image = Upload(
            required=True,
            description='Represents an image file in a multipart request.',
        )

    class Meta:
        description = '''
            Create a user avatar. Only for staff members. This mutation must
            be sent as a `multipart` request. More detailed specs of the
            upload format can be found here:
            https://github.com/jaydenseric/graphql-multipart-request-spec
            '''

    @classmethod
    @staff_member_required
    def perform_mutation(cls, _root, info, image):
        user = info.context.user
        image_data = info.context.FILES.get(image)
        validate_image_file(image_data, 'image')

        if user.avatar:
            user.avatar.delete_sized_images()
            user.avatar.delete()
        user.avatar = image_data
        user.save()
        create_user_avatar_thumbnails.delay(user_id=user.pk)

        return UserAvatarUpdate(user=user)


class UserAvatarDelete(BaseMutation):
    user = graphene.Field(User, description='An updated user instance.')

    class Meta:
        description = 'Deletes a user avatar. Only for staff members.'

    @classmethod
    @staff_member_required
    def perform_mutation(cls, _root, info):
        user = info.context.user
        user.avatar.delete_sized_images()
        user.avatar.delete()
        return UserAvatarDelete(user=user)

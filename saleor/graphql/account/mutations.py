import graphene
from django.contrib.auth.tokens import default_token_generator

from ...account import models
from ...core.permissions import MODELS_PERMISSIONS, get_permissions
from ..account.types import AddressInput
from ..core.mutations import ModelMutation


BILLING_ADDRESS_FIELD = 'default_billing_address'
SHIPPING_ADDRESS_FIELD = 'default_shipping_address'


class UserInput(graphene.InputObjectType):
    email = graphene.String(
        description='The unique email address of the user.')
    note = graphene.String(description='A note about the user.')


class CustomerInput(UserInput):
    default_billing_address = AddressInput(
        description='Billing address of the customer.')
    default_shipping_address = AddressInput(
        description='Shipping address of the customer.')


class StaffInput(UserInput):
    permissions = graphene.List(
        graphene.String,
        description='List of permission code names to assign to this user.')
    groups = graphene.List(
        graphene.ID,
        description='List of IDs of permission groups to assign the user to.')


class CustomerCreate(ModelMutation):
    class Arguments:
        input = CustomerInput(
            description='Fields required to create a customer.', required=True)

    class Meta:
        description = 'Creates a new customer.'
        exclude = ['password']
        model = models.User

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('account.edit_user')

    @classmethod
    def construct_address(
            cls, address_field_name, address_input, user_instance, errors):
        if not address_field_name in [
                BILLING_ADDRESS_FIELD, SHIPPING_ADDRESS_FIELD]:
            raise AssertionError(
                'Wrong address_field_name: %s' % address_field_name)

        address_instance = getattr(user_instance, address_field_name)
        if not address_instance:
            address_instance = models.Address()

        cls.construct_instance(address_instance, address_input)
        cls.clean_instance(address_instance, errors)
        return address_instance

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        shipping_address_input = input.pop(SHIPPING_ADDRESS_FIELD, None)
        billing_address_input = input.pop(BILLING_ADDRESS_FIELD, None)
        cleaned_input = super().clean_input(info, instance, input, errors)

        if shipping_address_input:
            shipping_address = cls.construct_address(
                SHIPPING_ADDRESS_FIELD, shipping_address_input, instance, errors)
            cleaned_input[SHIPPING_ADDRESS_FIELD] = shipping_address

        if billing_address_input:
            billing_address = cls.construct_address(
                BILLING_ADDRESS_FIELD, billing_address_input, instance, errors)
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


class StaffCreate(ModelMutation):
    class Arguments:
        input = StaffInput(
            description='Fields required to create a staff user.',
            required=True)

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

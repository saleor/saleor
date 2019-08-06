import graphene
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from ....account import events as account_events, models, utils
from ....checkout import AddressType
from ...account.enums import AddressTypeEnum
from ...account.types import Address, AddressInput, User
from ...core.mutations import BaseMutation, ModelMutation
from .base import BaseCustomerCreate, UserAddressInput, send_user_password_reset_email


class CustomerRegisterInput(graphene.InputObjectType):
    email = graphene.String(
        description="The unique email address of the user.", required=True
    )
    password = graphene.String(description="Password", required=True)


class CustomerRegister(ModelMutation):
    class Arguments:
        input = CustomerRegisterInput(
            description="Fields required to create a user.", required=True
        )

    class Meta:
        description = "DEPRECATED: Use AccountRegister instead. Register a new user."
        exclude = ["password"]
        model = models.User

    @classmethod
    def save(cls, info, user, cleaned_input):
        password = cleaned_input["password"]
        user.set_password(password)
        user.save()
        account_events.customer_account_created_event(user=user)


class LoggedUserUpdate(BaseCustomerCreate):
    class Arguments:
        input = UserAddressInput(
            description="Fields required to update a logged in user.", required=True
        )

    class Meta:
        description = (
            "DEPRECATED: Use AccountUpdate instead. "
            "Updates data of the logged in user."
        )
        exclude = ["password"]
        model = models.User

    @classmethod
    def check_permissions(cls, user):
        return user.is_authenticated

    @classmethod
    def perform_mutation(cls, root, info, **data):
        user = info.context.user
        data["id"] = graphene.Node.to_global_id("User", user.id)
        return super().perform_mutation(root, info, **data)


class CustomerAddressCreate(ModelMutation):
    user = graphene.Field(
        User, description="A user instance for which the address was created."
    )

    class Arguments:
        input = AddressInput(
            description="Fields required to create address", required=True
        )
        type = AddressTypeEnum(
            required=False,
            description=(
                "A type of address. If provided, the new address will be "
                "automatically assigned as the customer's default address "
                "of that type."
            ),
        )

    class Meta:
        description = (
            "DEPRECATED: Use AccountAddressCreate instead."
            "Create a new address for the customer."
        )
        model = models.Address
        exclude = ["user_addresses"]

    @classmethod
    def check_permissions(cls, user):
        return user.is_authenticated

    @classmethod
    def perform_mutation(cls, root, info, **data):
        success_response = super().perform_mutation(root, info, **data)
        address_type = data.get("type", None)
        if address_type:
            user = info.context.user
            instance = success_response.address
            utils.change_user_default_address(user, instance, address_type)
            success_response.user = user
        return success_response

    @classmethod
    def save(cls, info, instance, cleaned_input):
        super().save(info, instance, cleaned_input)
        user = info.context.user
        instance.user_addresses.add(user)


class CustomerSetDefaultAddress(BaseMutation):
    user = graphene.Field(User, description="An updated user instance.")

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of the address to set as default."
        )
        type = AddressTypeEnum(required=True, description="The type of address.")

    class Meta:
        description = (
            "DEPRECATED: Use AccountSetDefaultAddress instead."
            "Sets a default address for the authenticated user."
        )

    @classmethod
    def check_permissions(cls, user):
        return user.is_authenticated

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        address = cls.get_node_or_error(info, data.get("id"), Address)
        user = info.context.user

        if address not in user.addresses.all():
            raise ValidationError({"id": "The address doesn't belong to that user."})

        if data.get("type") == AddressTypeEnum.BILLING.value:
            address_type = AddressType.BILLING
        else:
            address_type = AddressType.SHIPPING

        utils.change_user_default_address(user, address, address_type)
        return cls(user=user)


class CustomerPasswordResetInput(graphene.InputObjectType):
    email = graphene.String(
        required=True,
        description=("Email of the user that will be used for password recovery."),
    )


class CustomerPasswordReset(BaseMutation):
    class Arguments:
        input = CustomerPasswordResetInput(
            description="Fields required to reset customer's password", required=True
        )

    class Meta:
        description = (
            "DEPRECATED: Use RequestPasswordReset instead."
            "Resets the customer's password."
        )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        email = data.get("input")["email"]
        try:
            user = models.User.objects.get(email=email)
        except ObjectDoesNotExist:
            raise ValidationError({"email": "User with this email doesn't exist"})
        site = info.context.site
        send_user_password_reset_email(user, site)
        return CustomerPasswordReset()

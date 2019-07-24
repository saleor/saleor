import graphene
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from ....account import emails, events as account_events, models, utils
from ....checkout import AddressType
from ...account.enums import AddressTypeEnum
from ...account.types import Address, AddressInput, User
from ...core.mutations import BaseMutation, ModelMutation
from .base import BaseAddressDelete, BaseAddressUpdate, send_user_password_reset_email
from .staff import CustomerCreate, UserAddressInput


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
        description = "Register a new user."
        exclude = ["password"]
        model = models.User

    @classmethod
    def save(cls, info, user, cleaned_input):
        password = cleaned_input["password"]
        user.set_password(password)
        user.save()
        account_events.customer_account_created_event(user=user)


class LoggedUserUpdate(CustomerCreate):
    class Arguments:
        input = UserAddressInput(
            description="Fields required to update logged in user.", required=True
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


class AccountInput(graphene.InputObjectType):
    first_name = graphene.String(description="Given name.")
    last_name = graphene.String(description="Family name.")
    default_billing_address = AddressInput(
        description="Billing address of the customer."
    )
    default_shipping_address = AddressInput(
        description="Shipping address of the customer."
    )


class AccountUpdate(CustomerCreate):
    class Arguments:
        input = AccountInput(
            description="Fields required to update the account of the logged-in user.",
            required=True,
        )

    class Meta:
        description = "Updates the account of the logged-in user."
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


class AccountRequestDeletion(BaseMutation):
    class Meta:
        description = (
            "Sends an email with the account removal link for the logged-in user."
        )

    @classmethod
    def check_permissions(cls, user):
        return user.is_authenticated

    @classmethod
    def perform_mutation(cls, root, info, **data):
        user = info.context.user
        emails.send_account_delete_confirmation_email.delay(str(user.token), user.email)
        return AccountRequestDeletion()


# The same as AddressCreate, but for the currently authenticated user.
class CustomerAddressCreate(ModelMutation):
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
        description = "Create a new address for the customer."
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
        return success_response

    @classmethod
    def save(cls, info, instance, cleaned_input):
        super().save(info, instance, cleaned_input)
        user = info.context.user
        instance.user_addresses.add(user)


class AccountAddressUpdate(BaseAddressUpdate):
    class Meta:
        description = "Updates an address of the logged-in user."
        model = models.Address
        exclude = ["user_addresses"]


class AccountAddressDelete(BaseAddressDelete):
    class Meta:
        description = "Delete an address of the logged-in user."
        model = models.Address


class AccountSetDefaultAddress(BaseMutation):
    user = graphene.Field(User, description="An updated user instance.")

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of the address to set as default."
        )
        type = AddressTypeEnum(required=True, description="The type of address.")

    class Meta:
        description = "Sets a default address for the authenticated user."

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


class CustomerSetDefaultAddress(AccountSetDefaultAddress):
    class Meta:
        description = (
            "DEPRECATED: Use SetPassword instead."
            "Sets a default address for the authenticated user."
        )


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
            "DEPRECATED: Use SetPassword instead. Resets the customer's password."
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

import graphene
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from graphql_jwt.exceptions import PermissionDenied

from ....account import emails, events as account_events, models
from ....dashboard.emails import send_set_password_customer_email
from ...account.i18n import I18nMixin
from ...account.types import Address, AddressInput, User
from ...core.mutations import (
    BaseMutation,
    ClearMetaBaseMutation,
    ModelDeleteMutation,
    ModelMutation,
    UpdateMetaBaseMutation,
)

BILLING_ADDRESS_FIELD = "default_billing_address"
SHIPPING_ADDRESS_FIELD = "default_shipping_address"
INVALID_TOKEN = "Invalid or expired token."


def send_user_password_reset_email(user, site):
    context = {
        "email": user.email,
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "token": default_token_generator.make_token(user),
        "site_name": site.name,
        "domain": site.domain,
        "protocol": "https" if settings.ENABLE_SSL else "http",
    }
    emails.send_password_reset_email.delay(context, user.email, user.pk)


def can_edit_address(user, address):
    """Determine whether the user can edit the given address.

    This method assumes that an address can be edited by:
    - users with proper permissions (staff)
    - customers associated to the given address.
    """
    return (
        user.has_perm("account.manage_users")
        or user.addresses.filter(pk=address.pk).exists()
    )


class SetPasswordInput(graphene.InputObjectType):
    token = graphene.String(
        description="A one-time token required to set the password.", required=True
    )
    password = graphene.String(description="Password", required=True)


class SetPassword(BaseMutation):
    user = graphene.Field(User, description="An user instance with new password.")

    class Arguments:
        email = graphene.String(
            required=True, description="Email of a user to set password whom."
        )
        input = SetPasswordInput(
            description="Fields required to set password.", required=True
        )

    class Meta:
        description = (
            "Sets the user's password from the token sent by email "
            "using the RequestPasswordReset mutation."
        )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        email = data["email"]
        try:
            user = models.User.objects.get(email=email)
        except ObjectDoesNotExist:
            raise ValidationError({"email": "User doesn't exist"})
        token = data["input"]["token"]
        if not default_token_generator.check_token(user, token):
            raise ValidationError({"token": INVALID_TOKEN})
        user.set_password(data["input"]["password"])
        user.save(update_fields=["password"])
        account_events.customer_password_reset_event(user=user)
        return cls(user=user)


class RequestPasswordReset(BaseMutation):
    class Arguments:
        email = graphene.String(
            required=True,
            description="Email of the user that will be used for password recovery.",
        )

    class Meta:
        description = "Sends an email with the account password modification link."

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        email = data["email"]
        try:
            user = models.User.objects.get(email=email)
        except ObjectDoesNotExist:
            raise ValidationError({"email": "User with this email doesn't exist"})
        site = info.context.site
        send_user_password_reset_email(user, site)
        return RequestPasswordReset()


class BaseAddressUpdate(ModelMutation):
    """Base mutation for address update used by staff and account."""

    user = graphene.Field(
        User, description="A user object for which the address was edited."
    )

    class Arguments:
        id = graphene.ID(description="ID of the address to update", required=True)
        input = AddressInput(
            description="Fields required to update the address", required=True
        )

    class Meta:
        abstract = True

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


class BaseAddressDelete(ModelDeleteMutation):
    """Base mutation for address delete used by staff and customers."""

    user = graphene.Field(
        User, description="A user instance for which the address was deleted."
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of the address to delete.")

    class Meta:
        abstract = True

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

        node_id = data.get("id")
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

        # Refresh the user instance to clear the default addresses. If the
        # deleted address was used as default, it would stay cached in the
        # user instance and the invalid ID returned in the response might cause
        # an error.
        user.refresh_from_db()

        response = cls.success_response(instance)

        response.user = user
        return response


class UserInput(graphene.InputObjectType):
    first_name = graphene.String(description="Given name.")
    last_name = graphene.String(description="Family name.")
    email = graphene.String(description="The unique email address of the user.")
    is_active = graphene.Boolean(required=False, description="User account is active.")
    note = graphene.String(description="A note about the user.")


class UserAddressInput(graphene.InputObjectType):
    default_billing_address = AddressInput(
        description="Billing address of the customer."
    )
    default_shipping_address = AddressInput(
        description="Shipping address of the customer."
    )


class CustomerInput(UserInput, UserAddressInput):
    pass


class UserCreateInput(CustomerInput):
    send_password_email = graphene.Boolean(
        description="Send an email with a link to set a password"
    )


class BaseCustomerCreate(ModelMutation, I18nMixin):
    """Base mutation for customer create used by staff and account."""

    class Arguments:
        input = UserCreateInput(
            description="Fields required to create a customer.", required=True
        )

    class Meta:
        abstract = True

    @classmethod
    def clean_input(cls, info, instance, data):
        shipping_address_data = data.pop(SHIPPING_ADDRESS_FIELD, None)
        billing_address_data = data.pop(BILLING_ADDRESS_FIELD, None)
        cleaned_input = super().clean_input(info, instance, data)

        if shipping_address_data:
            shipping_address = cls.validate_address(
                shipping_address_data,
                instance=getattr(instance, SHIPPING_ADDRESS_FIELD),
            )
            cleaned_input[SHIPPING_ADDRESS_FIELD] = shipping_address

        if billing_address_data:
            billing_address = cls.validate_address(
                billing_address_data, instance=getattr(instance, BILLING_ADDRESS_FIELD)
            )
            cleaned_input[BILLING_ADDRESS_FIELD] = billing_address
        return cleaned_input

    @classmethod
    @transaction.atomic
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

        is_creation = instance.pk is None
        super().save(info, instance, cleaned_input)

        # The instance is a new object in db, create an event
        if is_creation:
            account_events.customer_account_created_event(user=instance)

        if cleaned_input.get("send_password_email"):
            send_set_password_customer_email.delay(instance.pk)


class UserUpdateMeta(UpdateMetaBaseMutation):
    class Meta:
        description = "Updates metadata for user."
        model = models.User
        public = True


class UserClearStoredMeta(ClearMetaBaseMutation):
    class Meta:
        description = "Clear stored metadata value."
        model = models.User
        public = True

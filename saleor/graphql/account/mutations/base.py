import graphene
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from graphql_jwt.exceptions import PermissionDenied

from ....account import emails, events as account_events, models
from ...account.types import Address, AddressInput, User
from ...core.mutations import (
    ClearMetaBaseMutation,
    ModelDeleteMutation,
    ModelMutation,
    UpdateMetaBaseMutation,
)


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
    - users with proper permission (staff)
    - customers who "own" the given address.
    """
    has_perm = user.has_perm("account.manage_users")
    belongs_to_user = address in user.addresses.all()
    return has_perm or belongs_to_user


class SetPasswordInput(graphene.InputObjectType):
    token = graphene.String(
        description="A one-time token required to set the password.", required=True
    )
    password = graphene.String(description="Password", required=True)


class SetPassword(ModelMutation):
    INVALID_TOKEN = "Invalid or expired token."

    class Arguments:
        id = graphene.ID(
            description="ID of a user to set password whom.", required=True
        )
        input = SetPasswordInput(
            description="Fields required to set password.", required=True
        )

    class Meta:
        description = "Sets user password."
        model = models.User

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        token = cleaned_input.pop("token")
        if not default_token_generator.check_token(instance, token):
            raise ValidationError({"token": SetPassword.INVALID_TOKEN})
        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.set_password(cleaned_input["password"])
        instance.save()
        account_events.customer_password_reset_event(user=instance)


class BaseAddressUpdate(ModelMutation):
    """Base mutation for address update used by staff and account."""

    user = graphene.Field(
        User, description="A user instance for which the address was edited."
    )

    class Arguments:
        id = graphene.ID(description="ID of the address to update", required=True)
        input = AddressInput(
            description="Fields required to update address", required=True
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
    """Base mutation for address delete used by staff and account."""

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

        response = cls.success_response(instance)

        # Refresh the user instance to clear the default addresses. If the
        # deleted address was used as default, it would stay cached in the
        # user instance and the invalid ID returned in the response might cause
        # an error.
        user.refresh_from_db()

        response.user = user
        return response


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

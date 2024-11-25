from typing import cast

import graphene
from django.conf import settings
from django.contrib.auth import password_validation
from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils import timezone

from ....account import events as account_events
from ....account import models
from ....account.error_codes import AccountErrorCode
from ....account.notifications import (
    send_password_reset_notification,
    send_set_password_notification,
)
from ....account.search import prepare_user_search_document_value
from ....account.utils import retrieve_user_by_email
from ....checkout import AddressType
from ....core.exceptions import PermissionDenied
from ....core.tracing import traced_atomic_transaction
from ....core.utils.url import validate_storefront_url
from ....giftcard.utils import assign_user_gift_cards
from ....graphql.utils import get_user_or_app_from_context
from ....order.utils import match_orders_with_new_user
from ....permission.auth_filters import AuthorizationFilters
from ....permission.enums import AccountPermissions
from ...account.i18n import I18nMixin
from ...account.types import Address, AddressInput, User
from ...app.dataloaders import get_app_promise
from ...channel.utils import clean_channel, validate_channel
from ...core import ResolveInfo
from ...core.context import disallow_replica_in_context
from ...core.descriptions import ADDED_IN_310, ADDED_IN_314
from ...core.doc_category import DOC_CATEGORY_USERS
from ...core.enums import LanguageCodeEnum
from ...core.mutations import (
    BaseMutation,
    ModelDeleteMutation,
    ModelMutation,
    validation_error_to_error_type,
)
from ...core.types import AccountError, BaseInputObjectType, NonNullList
from ...meta.mutations import MetadataInput
from ...plugins.dataloaders import get_plugin_manager_promise
from .authentication import CreateToken

BILLING_ADDRESS_FIELD = "default_billing_address"
SHIPPING_ADDRESS_FIELD = "default_shipping_address"
INVALID_TOKEN = "Invalid or expired token."


def check_can_edit_address(context, address):
    """Determine whether the user or app can edit the given address.

    This method assumes that an address can be edited by:
    - apps with manage users permission
    - staff with manage users permission
    - customers associated to the given address.
    """
    requester = get_user_or_app_from_context(context)
    if requester and requester.has_perm(AccountPermissions.MANAGE_USERS):
        return True
    app = get_app_promise(context).get()
    if not app and context.user:
        is_owner = context.user.addresses.filter(pk=address.pk).exists()
        if is_owner:
            return True
    raise PermissionDenied(
        permissions=[AccountPermissions.MANAGE_USERS, AuthorizationFilters.OWNER]
    )


class SetPassword(CreateToken):
    class Arguments:
        token = graphene.String(
            description="A one-time token required to set the password.", required=True
        )
        email = graphene.String(required=True, description="Email of a user.")
        password = graphene.String(required=True, description="Password of a user.")

    class Meta:
        description = (
            "Sets the user's password from the token sent by email "
            "using the RequestPasswordReset mutation."
        )
        doc_category = DOC_CATEGORY_USERS
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def mutate(  # type: ignore[override]
        cls, root, info: ResolveInfo, /, *, email, password, token
    ):
        disallow_replica_in_context(info.context)
        manager = get_plugin_manager_promise(info.context).get()
        result = manager.perform_mutation(
            mutation_cls=cls,
            root=root,
            info=info,
            data={"email": email, "password": password, "token": token},
        )
        if result is not None:
            return result

        try:
            cls._set_password_for_user(email, password, token)
        except ValidationError as e:
            errors = validation_error_to_error_type(e, AccountError)
            return cls.handle_typed_errors(errors)
        return super().mutate(root, info, email=email, password=password)

    @classmethod
    def _set_password_for_user(cls, email, password, token):
        try:
            user = models.User.objects.get(email=email)
        except ObjectDoesNotExist:
            raise ValidationError(
                {
                    "email": ValidationError(
                        "User doesn't exist", code=AccountErrorCode.NOT_FOUND.value
                    )
                }
            )
        if not default_token_generator.check_token(user, token):
            raise ValidationError(
                {
                    "token": ValidationError(
                        INVALID_TOKEN, code=AccountErrorCode.INVALID.value
                    )
                }
            )
        try:
            password_validation.validate_password(password, user)
        except ValidationError as error:
            raise ValidationError({"password": error})
        user.set_password(password)
        user.save(update_fields=["password", "updated_at"])
        account_events.customer_password_reset_event(user=user)


class RequestPasswordReset(BaseMutation):
    class Arguments:
        email = graphene.String(
            required=True,
            description="Email of the user that will be used for password recovery.",
        )
        redirect_url = graphene.String(
            required=True,
            description=(
                "URL of a view where users should be redirected to "
                "reset the password. URL in RFC 1808 format."
            ),
        )
        channel = graphene.String(
            description=(
                "Slug of a channel which will be used for notify user. Optional when "
                "only one channel exists."
            )
        )

    class Meta:
        description = "Sends an email with the account password modification link."
        doc_category = DOC_CATEGORY_USERS
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def clean_user(cls, email, redirect_url):
        try:
            validate_storefront_url(redirect_url)
        except ValidationError as error:
            raise ValidationError(
                {"redirect_url": error}, code=AccountErrorCode.INVALID.value
            )

        user = retrieve_user_by_email(email)
        if not user:
            raise ValidationError(
                {
                    "email": ValidationError(
                        "User with this email doesn't exist",
                        code=AccountErrorCode.NOT_FOUND.value,
                    )
                }
            )

        if not user.is_active:
            raise ValidationError(
                {
                    "email": ValidationError(
                        "User with this email is inactive",
                        code=AccountErrorCode.INACTIVE.value,
                    )
                }
            )

        if password_reset_time := user.last_password_reset_request:
            delta = timezone.now() - password_reset_time
            if delta.total_seconds() < settings.RESET_PASSWORD_LOCK_TIME:
                raise ValidationError(
                    {
                        "email": ValidationError(
                            "Password reset already requested",
                            code=AccountErrorCode.PASSWORD_RESET_ALREADY_REQUESTED.value,
                        )
                    }
                )

        return user

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        email = data["email"]
        redirect_url = data["redirect_url"]
        channel_slug = data.get("channel")
        user = cls.clean_user(email, redirect_url)

        if not user.is_staff:
            channel_slug = clean_channel(
                channel_slug, error_class=AccountErrorCode
            ).slug
        elif channel_slug is not None:
            channel_slug = validate_channel(
                channel_slug, error_class=AccountErrorCode
            ).slug
        manager = get_plugin_manager_promise(info.context).get()
        send_password_reset_notification(
            redirect_url,
            user,
            manager,
            channel_slug=channel_slug,
            staff=user.is_staff,
        )
        user.last_password_reset_request = timezone.now()
        user.save(update_fields=["last_password_reset_request"])
        return RequestPasswordReset()


class ConfirmAccount(BaseMutation):
    user = graphene.Field(User, description="An activated user account.")

    class Arguments:
        token = graphene.String(
            description="A one-time token required to confirm the account.",
            required=True,
        )
        email = graphene.String(
            description="E-mail of the user performing account confirmation.",
            required=True,
        )

    class Meta:
        description = (
            "Confirm user account with token sent by email during registration."
        )
        doc_category = DOC_CATEGORY_USERS
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        try:
            user = models.User.objects.get(email=data["email"])
        except ObjectDoesNotExist:
            raise ValidationError(
                {
                    "email": ValidationError(
                        "User with this email doesn't exist",
                        code=AccountErrorCode.NOT_FOUND.value,
                    )
                }
            )

        if not default_token_generator.check_token(user, data["token"]):
            raise ValidationError(
                {
                    "token": ValidationError(
                        INVALID_TOKEN, code=AccountErrorCode.INVALID.value
                    )
                }
            )

        user.is_active = True
        user.is_confirmed = True
        user.save(update_fields=["is_active", "is_confirmed", "updated_at"])

        match_orders_with_new_user(user)
        assign_user_gift_cards(user)

        return ConfirmAccount(user=user)


class PasswordChange(BaseMutation):
    user = graphene.Field(User, description="A user instance with a new password.")

    class Arguments:
        old_password = graphene.String(
            required=False, description="Current user password."
        )
        new_password = graphene.String(required=True, description="New user password.")

    class Meta:
        description = "Change the password of the logged in user."
        doc_category = DOC_CATEGORY_USERS
        error_type_class = AccountError
        error_type_field = "account_errors"
        permissions = (AuthorizationFilters.AUTHENTICATED_USER,)

    @staticmethod
    def raise_invalid_credentials():
        raise ValidationError(
            {
                "old_password": ValidationError(
                    "Old password isn't valid.",
                    code=AccountErrorCode.INVALID_CREDENTIALS.value,
                )
            }
        )

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        user = info.context.user
        user = cast(models.User, user)
        old_password = data.get("old_password")
        new_password = data["new_password"]

        if old_password is None:
            # Spend time hashing useless password
            # This prevents the outside actors from telling if user has
            # unusable password set or not by measuring API's response time
            make_password("waste-time")

            if user.has_usable_password():
                cls.raise_invalid_credentials()
        elif not user.check_password(old_password):
            cls.raise_invalid_credentials()
        try:
            password_validation.validate_password(new_password, user)
        except ValidationError as error:
            raise ValidationError({"new_password": error})

        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])
        account_events.customer_password_changed_event(user=user)
        return PasswordChange(user=user)


class BaseAddressUpdate(ModelMutation, I18nMixin):
    """Base mutation for address update used by staff and account."""

    user = graphene.Field(
        User, description="A user object for which the address was edited."
    )

    class Arguments:
        id = graphene.ID(description="ID of the address to update.", required=True)
        input = AddressInput(
            description="Fields required to update the address.", required=True
        )

    class Meta:
        abstract = True

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        # Method check_permissions cannot be used for permission check, because
        # it doesn't have the address instance.
        check_can_edit_address(info.context, instance)
        return super().clean_input(info, instance, data, **kwargs)

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        instance = cls.get_instance(info, **data)
        cleaned_input = cls.clean_input(
            info=info, instance=instance, data=data.get("input")
        )
        address = cls.validate_address(cleaned_input, instance=instance)
        cls.clean_instance(info, address)
        cls.save(info, address, cleaned_input)
        cls._save_m2m(info, address, cleaned_input)

        user = address.user_addresses.first()
        if user:
            user.search_document = prepare_user_search_document_value(user)
            user.save(update_fields=["search_document", "updated_at"])
        manager = get_plugin_manager_promise(info.context).get()
        address = manager.change_user_address(address, None, user)
        cls.call_event(manager.address_updated, address)

        success_response = cls.success_response(address)
        success_response.user = user
        success_response.address = address
        return success_response


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
    def clean_instance(cls, info: ResolveInfo, instance) -> None:
        # Method check_permissions cannot be used for permission check, because
        # it doesn't have the address instance.
        check_can_edit_address(info.context, instance)
        return super().clean_instance(info, instance)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str
    ):
        if not cls.check_permissions(info.context):
            raise PermissionDenied()

        instance = cls.get_node_or_error(info, id, only_type=Address)
        if instance:
            cls.clean_instance(info, instance)

        db_id = instance.id

        # Return the first user that the address is assigned to. There is M2M
        # relation between users and addresses, but in most cases address is
        # related to only one user.
        user = instance.user_addresses.first()

        instance.delete()
        instance.id = db_id

        if user:
            # Refresh the user instance to clear the default addresses. If the
            # deleted address was used as default, it would stay cached in the
            # user instance and the invalid ID returned in the response might cause
            # an error.
            user.refresh_from_db()

            user.search_document = prepare_user_search_document_value(user)
            user.save(update_fields=["search_document", "updated_at"])

        response = cls.success_response(instance)

        response.user = user
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.address_deleted, instance)
        return response


class UserInput(BaseInputObjectType):
    first_name = graphene.String(description="Given name.")
    last_name = graphene.String(description="Family name.")
    email = graphene.String(description="The unique email address of the user.")
    is_active = graphene.Boolean(required=False, description="User account is active.")
    note = graphene.String(description="A note about the user.")
    metadata = NonNullList(
        MetadataInput,
        description="Fields required to update the user metadata." + ADDED_IN_314,
        required=False,
    )
    private_metadata = NonNullList(
        MetadataInput,
        description=(
            "Fields required to update the user private metadata." + ADDED_IN_314
        ),
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_USERS


class UserAddressInput(BaseInputObjectType):
    default_billing_address = AddressInput(
        description="Billing address of the customer."
    )
    default_shipping_address = AddressInput(
        description="Shipping address of the customer."
    )

    class Meta:
        doc_category = DOC_CATEGORY_USERS


class CustomerInput(UserInput, UserAddressInput):
    language_code = graphene.Field(
        LanguageCodeEnum, required=False, description="User language code."
    )
    external_reference = graphene.String(
        description="External ID of the customer." + ADDED_IN_310, required=False
    )

    class Meta:
        doc_category = DOC_CATEGORY_USERS


class UserCreateInput(CustomerInput):
    redirect_url = graphene.String(
        description=(
            "URL of a view where users should be redirected to "
            "set the password. URL in RFC 1808 format."
        )
    )
    channel = graphene.String(
        description=(
            "Slug of a channel which will be used for notify user. Optional when "
            "only one channel exists."
        )
    )

    class Meta:
        doc_category = DOC_CATEGORY_USERS


class BaseCustomerCreate(ModelMutation, I18nMixin):
    """Base mutation for customer create used by staff and account."""

    class Arguments:
        input = UserCreateInput(
            description="Fields required to create a customer.", required=True
        )

    class Meta:
        abstract = True

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        shipping_address_data = data.pop(SHIPPING_ADDRESS_FIELD, None)
        billing_address_data = data.pop(BILLING_ADDRESS_FIELD, None)
        cleaned_input = super().clean_input(info, instance, data, **kwargs)

        if shipping_address_data:
            shipping_address = cls.validate_address(
                shipping_address_data,
                address_type=AddressType.SHIPPING,
                instance=getattr(instance, SHIPPING_ADDRESS_FIELD),
                info=info,
            )
            cleaned_input[SHIPPING_ADDRESS_FIELD] = shipping_address

        if billing_address_data:
            billing_address = cls.validate_address(
                billing_address_data,
                address_type=AddressType.BILLING,
                instance=getattr(instance, BILLING_ADDRESS_FIELD),
                info=info,
            )
            cleaned_input[BILLING_ADDRESS_FIELD] = billing_address

        if cleaned_input.get("redirect_url"):
            try:
                validate_storefront_url(cleaned_input.get("redirect_url"))
            except ValidationError as error:
                raise ValidationError(
                    {"redirect_url": error}, code=AccountErrorCode.INVALID.value
                )

        email = cleaned_input.get("email")
        if email:
            cleaned_input["email"] = email.lower()

        return cleaned_input

    @classmethod
    @traced_atomic_transaction()
    def save(cls, info: ResolveInfo, instance, cleaned_input):
        default_shipping_address = cleaned_input.get(SHIPPING_ADDRESS_FIELD)
        manager = get_plugin_manager_promise(info.context).get()
        if default_shipping_address:
            default_shipping_address = manager.change_user_address(
                default_shipping_address, "shipping", instance
            )
            default_shipping_address.save()
            instance.default_shipping_address = default_shipping_address
        default_billing_address = cleaned_input.get(BILLING_ADDRESS_FIELD)
        if default_billing_address:
            default_billing_address = manager.change_user_address(
                default_billing_address, "billing", instance
            )
            default_billing_address.save()
            instance.default_billing_address = default_billing_address

        is_creation = instance.pk is None
        super().save(info, instance, cleaned_input)
        if default_billing_address:
            instance.addresses.add(default_billing_address)
        if default_shipping_address:
            instance.addresses.add(default_shipping_address)

        instance.search_document = prepare_user_search_document_value(instance)
        instance.save(update_fields=["search_document", "updated_at"])

        # The instance is a new object in db, create an event
        if is_creation:
            cls.call_event(manager.customer_created, instance)
            account_events.customer_account_created_event(user=instance)
        else:
            cls.call_event(manager.customer_updated, instance)

        if cleaned_input.get("redirect_url"):
            channel_slug = cleaned_input.get("channel")
            if not instance.is_staff:
                channel_slug = clean_channel(
                    channel_slug, error_class=AccountErrorCode
                ).slug
            elif channel_slug is not None:
                channel_slug = validate_channel(
                    channel_slug, error_class=AccountErrorCode
                ).slug
            send_set_password_notification(
                cleaned_input.get("redirect_url"),
                instance,
                manager,
                channel_slug,
            )

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        if cleaned_input.get("metadata"):
            manager = get_plugin_manager_promise(info.context).get()
            cls.call_event(manager.customer_metadata_updated, instance)

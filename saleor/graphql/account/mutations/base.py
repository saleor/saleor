from collections import defaultdict
from typing import List

import graphene
from django.core.exceptions import ValidationError

from ....account import events as account_events
from ....account.error_codes import AccountErrorCode
from ....account.notifications import send_set_password_notification
from ....account.search import prepare_user_search_document_value
from ....checkout import AddressType
from ....core.exceptions import PermissionDenied
from ....core.tracing import traced_atomic_transaction
from ....core.utils.url import validate_storefront_url
from ....giftcard.search import mark_gift_cards_search_index_as_dirty
from ....giftcard.utils import get_user_gift_cards
from ....graphql.utils import get_user_or_app_from_context
from ....permission.auth_filters import AuthorizationFilters
from ....permission.enums import AccountPermissions
from ...account.i18n import I18nMixin
from ...account.types import Address, AddressInput, User
from ...app.dataloaders import get_app_promise
from ...channel.utils import clean_channel, validate_channel
from ...core import ResolveInfo, SaleorContext
from ...core.descriptions import ADDED_IN_310, ADDED_IN_314
from ...core.doc_category import DOC_CATEGORY_USERS
from ...core.enums import LanguageCodeEnum
from ...core.mutations import ModelDeleteMutation, ModelMutation
from ...core.types import BaseInputObjectType, NonNullList
from ...meta.inputs import MetadataInput
from ...plugins.dataloaders import get_plugin_manager_promise
from ..utils import (
    get_not_manageable_permissions_when_deactivate_or_remove_users,
    get_out_of_scope_users,
)

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
            manager.customer_updated(instance)

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

        if cleaned_input.get("first_name") or cleaned_input.get("last_name"):
            if user_gift_cards := get_user_gift_cards(instance):
                mark_gift_cards_search_index_as_dirty(user_gift_cards)


class UserDeleteMixin:
    class Meta:
        abstract = True

    @classmethod
    def clean_instance(cls, info: ResolveInfo, instance) -> None:
        user = info.context.user
        if instance == user:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "You cannot delete your own account.",
                        code=AccountErrorCode.DELETE_OWN_ACCOUNT.value,
                    )
                }
            )
        elif instance.is_superuser:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Cannot delete this account.",
                        code=AccountErrorCode.DELETE_SUPERUSER_ACCOUNT.value,
                    )
                }
            )


class CustomerDeleteMixin(UserDeleteMixin):
    class Meta:
        abstract = True

    @classmethod
    def clean_instance(cls, info: ResolveInfo, instance) -> None:
        super().clean_instance(info, instance)
        if instance.is_staff:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Cannot delete a staff account.",
                        code=AccountErrorCode.DELETE_STAFF_ACCOUNT.value,
                    )
                }
            )

    @classmethod
    def post_process(cls, info: ResolveInfo, deleted_count=1):
        app = get_app_promise(info.context).get()
        account_events.customer_deleted_event(
            staff_user=info.context.user,
            app=app,
            deleted_count=deleted_count,
        )


class StaffDeleteMixin(UserDeleteMixin):
    class Meta:
        abstract = True

    @classmethod
    def check_permissions(cls, context: SaleorContext, permissions=None, **data):
        if get_app_promise(context).get():
            raise PermissionDenied(
                message="Apps are not allowed to perform this mutation."
            )
        return super().check_permissions(context, permissions)  # type: ignore[misc] # mixin # noqa: E501

    @classmethod
    def clean_instance(cls, info: ResolveInfo, instance):
        errors: defaultdict[str, List[ValidationError]] = defaultdict(list)

        requestor = info.context.user

        cls.check_if_users_can_be_deleted(info, [instance], "id", errors)
        cls.check_if_requestor_can_manage_users(requestor, [instance], "id", errors)
        cls.check_if_removing_left_not_manageable_permissions(
            requestor, [instance], "id", errors
        )
        if errors:
            raise ValidationError(errors)

    @classmethod
    def check_if_users_can_be_deleted(cls, info: ResolveInfo, instances, field, errors):
        """Check if only staff users will be deleted. Cannot delete non-staff users."""
        not_staff_users = set()
        for user in instances:
            if not user.is_staff:
                not_staff_users.add(user)
            try:
                super().clean_instance(info, user)
            except ValidationError as error:
                errors["ids"].append(error)

        if not_staff_users:
            user_pks = [
                graphene.Node.to_global_id("User", user.pk) for user in not_staff_users
            ]
            msg = "Cannot delete a non-staff users."
            code = AccountErrorCode.DELETE_NON_STAFF_USER.value
            params = {"users": user_pks}
            errors[field].append(ValidationError(msg, code=code, params=params))

    @classmethod
    def check_if_requestor_can_manage_users(cls, requestor, instances, field, errors):
        """Requestor can't manage users with wider scope of permissions."""
        if requestor.is_superuser:
            return
        out_of_scope_users = get_out_of_scope_users(requestor, instances)
        if out_of_scope_users:
            user_pks = [
                graphene.Node.to_global_id("User", user.pk)
                for user in out_of_scope_users
            ]
            msg = "You can't manage this users."
            code = AccountErrorCode.OUT_OF_SCOPE_USER.value
            params = {"users": user_pks}
            error = ValidationError(msg, code=code, params=params)
            errors[field] = error

    @classmethod
    def check_if_removing_left_not_manageable_permissions(
        cls, requestor, users, field, errors: defaultdict[str, List[ValidationError]]
    ):
        """Check if after removing users all permissions will be manageable.

        After removing users, for each permission, there should be at least one
        active staff member who can manage it (has both “manage staff” and
        this permission).
        """
        if requestor.is_superuser:
            return
        permissions = get_not_manageable_permissions_when_deactivate_or_remove_users(
            users
        )
        if permissions:
            # add error
            msg = "Users cannot be removed, some of permissions will not be manageable."
            code = AccountErrorCode.LEFT_NOT_MANAGEABLE_PERMISSION.value
            params = {"permissions": permissions}
            error = ValidationError(msg, code=code, params=params)
            errors[field] = [error]

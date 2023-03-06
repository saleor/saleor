from collections import defaultdict
from copy import copy
from typing import cast

import graphene
from django.core.exceptions import ValidationError

from ....account import events as account_events
from ....account import models, utils
from ....account.error_codes import AccountErrorCode
from ....account.notifications import send_set_password_notification
from ....account.search import USER_SEARCH_FIELDS, prepare_user_search_document_value
from ....account.utils import (
    remove_staff_member,
    remove_the_oldest_user_address_if_address_limit_is_reached,
)
from ....checkout import AddressType
from ....core.exceptions import PermissionDenied
from ....core.permissions import AccountPermissions, AuthorizationFilters
from ....core.tracing import traced_atomic_transaction
from ....core.utils.url import validate_storefront_url
from ....giftcard.utils import assign_user_gift_cards
from ....order.utils import match_orders_with_new_user
from ....thumbnail import models as thumbnail_models
from ...account.enums import AddressTypeEnum
from ...account.types import Address, AddressInput, User
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_310
from ...core.mutations import (
    BaseMutation,
    ModelDeleteMutation,
    ModelMutation,
    ModelWithExtRefMutation,
)
from ...core.types import AccountError, NonNullList, StaffError, Upload
from ...core.validators.file import clean_image_file
from ...plugins.dataloaders import get_plugin_manager_promise
from ...utils.validators import check_for_duplicates
from ..utils import (
    CustomerDeleteMixin,
    StaffDeleteMixin,
    UserDeleteMixin,
    get_groups_which_user_can_manage,
    get_not_manageable_permissions_when_deactivate_or_remove_users,
    get_out_of_scope_users,
)
from .base import (
    BaseAddressDelete,
    BaseAddressUpdate,
    BaseCustomerCreate,
    CustomerInput,
    UserInput,
)


class StaffInput(UserInput):
    add_groups = NonNullList(
        graphene.ID,
        description="List of permission group IDs to which user should be assigned.",
        required=False,
    )


class StaffCreateInput(StaffInput):
    redirect_url = graphene.String(
        description=(
            "URL of a view where users should be redirected to "
            "set the password. URL in RFC 1808 format."
        )
    )


class StaffUpdateInput(StaffInput):
    remove_groups = NonNullList(
        graphene.ID,
        description=(
            "List of permission group IDs from which user should be unassigned."
        ),
        required=False,
    )


class CustomerCreate(BaseCustomerCreate):
    class Meta:
        description = "Creates a new customer."
        exclude = ["password"]
        model = models.User
        object_type = User
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"


class CustomerUpdate(CustomerCreate, ModelWithExtRefMutation):
    class Arguments:
        id = graphene.ID(description="ID of a customer to update.", required=False)
        external_reference = graphene.String(
            required=False,
            description=f"External ID of a customer to update. {ADDED_IN_310}",
        )
        input = CustomerInput(
            description="Fields required to update a customer.", required=True
        )

    class Meta:
        description = "Updates an existing customer."
        exclude = ["password"]
        model = models.User
        object_type = User
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def generate_events(
        cls, info: ResolveInfo, old_instance: models.User, new_instance: models.User
    ):
        # Retrieve the event base data
        staff_user = info.context.user
        app = get_app_promise(info.context).get()
        new_email = new_instance.email
        new_fullname = new_instance.get_full_name()

        # Compare the data
        has_new_name = old_instance.get_full_name() != new_fullname
        has_new_email = old_instance.email != new_email
        was_activated = not old_instance.is_active and new_instance.is_active
        was_deactivated = old_instance.is_active and not new_instance.is_active

        # Generate the events accordingly
        if has_new_email:
            account_events.assigned_email_to_a_customer_event(
                staff_user=staff_user, app=app, new_email=new_email
            )
            assign_user_gift_cards(new_instance)
            match_orders_with_new_user(new_instance)
        if has_new_name:
            account_events.assigned_name_to_a_customer_event(
                staff_user=staff_user, app=app, new_name=new_fullname
            )
        if was_activated:
            account_events.customer_account_activated_event(
                staff_user=info.context.user,
                app=app,
                account_id=old_instance.id,
            )
        if was_deactivated:
            account_events.customer_account_deactivated_event(
                staff_user=info.context.user,
                app=app,
                account_id=old_instance.id,
            )

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        """Generate events by comparing the old instance with the new data.

        It overrides the `perform_mutation` base method of ModelMutation.
        """

        # Retrieve the data
        original_instance = cls.get_instance(info, **data)
        data = data.get("input")

        # Clean the input and generate a new instance from the new data
        cleaned_input = cls.clean_input(info, original_instance, data)
        new_instance = cls.construct_instance(copy(original_instance), cleaned_input)

        # Save the new instance data
        cls.clean_instance(info, new_instance)
        cls.save(info, new_instance, cleaned_input)
        cls._save_m2m(info, new_instance, cleaned_input)

        # Generate events by comparing the instances
        cls.generate_events(info, original_instance, new_instance)

        # Return the response
        return cls.success_response(new_instance)


class UserDelete(UserDeleteMixin, ModelDeleteMutation, ModelWithExtRefMutation):
    class Meta:
        abstract = True


class CustomerDelete(CustomerDeleteMixin, UserDelete):
    class Meta:
        description = "Deletes a customer."
        model = models.User
        object_type = User
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    class Arguments:
        id = graphene.ID(required=False, description="ID of a customer to delete.")
        external_reference = graphene.String(
            required=False,
            description=f"External ID of a customer to update. {ADDED_IN_310}",
        )

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        results = super().perform_mutation(root, info, **data)
        cls.post_process(info)
        return results

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.customer_deleted, instance)


class StaffCreate(ModelMutation):
    class Arguments:
        input = StaffCreateInput(
            description="Fields required to create a staff user.", required=True
        )

    class Meta:
        description = (
            "Creates a new staff user. "
            "Apps are not allowed to perform this mutation."
        )
        exclude = ["password"]
        model = models.User
        object_type = User
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = StaffError
        error_type_field = "staff_errors"

    @classmethod
    def check_permissions(cls, context, permissions=None):
        app = get_app_promise(context).get()
        if app:
            raise PermissionDenied(
                message="Apps are not allowed to perform this mutation."
            )
        return super().check_permissions(context, permissions)

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)

        errors = defaultdict(list)
        if cleaned_input.get("redirect_url"):
            try:
                validate_storefront_url(cleaned_input.get("redirect_url"))
            except ValidationError as error:
                error.code = AccountErrorCode.INVALID.value
                errors["redirect_url"].append(error)

        user = info.context.user
        user = cast(models.User, user)
        # set is_staff to True to create a staff user
        cleaned_input["is_staff"] = True
        cls.clean_groups(user, cleaned_input, errors)
        cls.clean_is_active(cleaned_input, instance, info.context.user, errors)

        email = cleaned_input.get("email")
        if email:
            cleaned_input["email"] = email.lower()

        if errors:
            raise ValidationError(errors)

        return cleaned_input

    @classmethod
    def clean_groups(cls, requestor: models.User, cleaned_input: dict, errors: dict):
        if cleaned_input.get("add_groups"):
            cls.ensure_requestor_can_manage_groups(
                requestor, cleaned_input, "add_groups", errors
            )

    @classmethod
    def ensure_requestor_can_manage_groups(
        cls, requestor: models.User, cleaned_input: dict, field: str, errors: dict
    ):
        """Check if requestor can manage group.

        Requestor cannot manage group with wider scope of permissions.
        """
        if requestor.is_superuser:
            return
        groups = cleaned_input[field]
        user_editable_groups = get_groups_which_user_can_manage(requestor)
        out_of_scope_groups = set(groups) - set(user_editable_groups)
        if out_of_scope_groups:
            # add error
            ids = [
                graphene.Node.to_global_id("Group", group.pk)
                for group in out_of_scope_groups
            ]
            error_msg = "You can't manage these groups."
            code = AccountErrorCode.OUT_OF_SCOPE_GROUP.value
            params = {"groups": ids}
            error = ValidationError(message=error_msg, code=code, params=params)
            errors[field].append(error)

    @classmethod
    def clean_is_active(cls, cleaned_input, instance, request, errors):
        pass

    @classmethod
    def save(cls, info: ResolveInfo, user, cleaned_input, send_notification=True):
        if any([field in cleaned_input for field in USER_SEARCH_FIELDS]):
            user.search_document = prepare_user_search_document_value(
                user, attach_addresses_data=False
            )
        user.save()
        if cleaned_input.get("redirect_url") and send_notification:
            manager = get_plugin_manager_promise(info.context).get()
            send_set_password_notification(
                redirect_url=cleaned_input.get("redirect_url"),
                user=user,
                manager=manager,
                channel_slug=None,
                staff=True,
            )

    @classmethod
    def _save_m2m(cls, info: ResolveInfo, instance, cleaned_data):
        with traced_atomic_transaction():
            super()._save_m2m(info, instance, cleaned_data)
            groups = cleaned_data.get("add_groups")
            if groups:
                instance.groups.add(*groups)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.staff_created, instance)

    @classmethod
    def get_instance(cls, info: ResolveInfo, **data):
        object_id = data.get("id")
        email = data.get("input", {}).get("email")
        send_notification = True

        if (
            not object_id
            and email
            and (
                user := models.User.objects.filter(email=email, is_staff=False).first()
            )
        ):
            send_notification = False
            return user, send_notification
        return super().get_instance(info, **data), send_notification

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        instance, send_notification = cls.get_instance(info, **data)
        data = data.get("input")
        cleaned_input = cls.clean_input(info, instance, data)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(info, instance)
        cls.save(info, instance, cleaned_input, send_notification)
        cls._save_m2m(info, instance, cleaned_input)
        cls.post_save_action(info, instance, cleaned_input)
        return cls.success_response(instance)


class StaffUpdate(StaffCreate):
    class Arguments:
        id = graphene.ID(description="ID of a staff user to update.", required=True)
        input = StaffUpdateInput(
            description="Fields required to update a staff user.", required=True
        )

    class Meta:
        description = (
            "Updates an existing staff user. "
            "Apps are not allowed to perform this mutation."
        )
        exclude = ["password"]
        model = models.User
        object_type = User
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = StaffError
        error_type_field = "staff_errors"

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        user = info.context.user
        user = cast(models.User, user)
        # check if user can manage this user
        if not user.is_superuser and get_out_of_scope_users(user, [instance]):
            msg = "You can't manage this user."
            code = AccountErrorCode.OUT_OF_SCOPE_USER.value
            raise ValidationError({"id": ValidationError(msg, code=code)})

        error = check_for_duplicates(data, "add_groups", "remove_groups", "groups")
        if error:
            error.code = AccountErrorCode.DUPLICATED_INPUT_ITEM.value
            raise error

        cleaned_input = super().clean_input(info, instance, data, **kwargs)

        return cleaned_input

    @classmethod
    def clean_groups(cls, requestor: models.User, cleaned_input: dict, errors: dict):
        if cleaned_input.get("add_groups"):
            cls.ensure_requestor_can_manage_groups(
                requestor, cleaned_input, "add_groups", errors
            )
        if cleaned_input.get("remove_groups"):
            cls.ensure_requestor_can_manage_groups(
                requestor, cleaned_input, "remove_groups", errors
            )

    @classmethod
    def clean_is_active(
        cls,
        cleaned_input: dict,
        instance: models.User,
        requestor: models.User,
        errors: dict,
    ):
        is_active = cleaned_input.get("is_active")
        if is_active is None:
            return
        if not is_active:
            cls.check_if_deactivating_superuser_or_own_account(
                instance, requestor, errors
            )
            cls.check_if_deactivating_left_not_manageable_permissions(
                instance, requestor, errors
            )

    @classmethod
    def check_if_deactivating_superuser_or_own_account(
        cls, instance: models.User, requestor: models.User, errors: dict
    ):
        """User cannot deactivate superuser or own account.

        Args:
            instance: user instance which is going to deactivated
            requestor: user who performs the mutation
            errors: a dictionary to accumulate mutation errors

        """
        if requestor == instance:
            error = ValidationError(
                "Cannot deactivate your own account.",
                code=AccountErrorCode.DEACTIVATE_OWN_ACCOUNT.value,
            )
            errors["is_active"].append(error)
        elif instance.is_superuser:
            error = ValidationError(
                "Cannot deactivate superuser's account.",
                code=AccountErrorCode.DEACTIVATE_SUPERUSER_ACCOUNT.value,
            )
            errors["is_active"].append(error)

    @classmethod
    def check_if_deactivating_left_not_manageable_permissions(
        cls, user: models.User, requestor: models.User, errors: dict
    ):
        """Check if after deactivating user all permissions will be manageable.

        After deactivating user, for each permission, there should be at least one
        active staff member who can manage it (has both “manage staff” and
        this permission).
        """
        if requestor.is_superuser:
            return
        permissions = get_not_manageable_permissions_when_deactivate_or_remove_users(
            [user]
        )
        if permissions:
            # add error
            msg = (
                "Users cannot be deactivated, some of permissions "
                "will not be manageable."
            )
            code = AccountErrorCode.LEFT_NOT_MANAGEABLE_PERMISSION.value
            params = {"permissions": permissions}
            error = ValidationError(msg, code=code, params=params)
            errors["is_active"].append(error)

    @classmethod
    def _save_m2m(cls, info: ResolveInfo, instance, cleaned_data):
        with traced_atomic_transaction():
            super()._save_m2m(info, instance, cleaned_data)
            add_groups = cleaned_data.get("add_groups")
            if add_groups:
                instance.groups.add(*add_groups)
            remove_groups = cleaned_data.get("remove_groups")
            if remove_groups:
                instance.groups.remove(*remove_groups)

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        instance, _ = cls.get_instance(info, **data)
        old_email = instance.email
        response = super().perform_mutation(root, info, **data)
        user = response.user
        if user.email != old_email:
            assign_user_gift_cards(user)
            match_orders_with_new_user(user)
        return response

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.staff_updated, instance)


class StaffDelete(StaffDeleteMixin, UserDelete):
    class Meta:
        description = (
            "Deletes a staff user. Apps are not allowed to perform this mutation."
        )
        model = models.User
        object_type = User
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = StaffError
        error_type_field = "staff_errors"

    class Arguments:
        id = graphene.ID(required=True, description="ID of a staff user to delete.")

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str
    ):
        instance = cls.get_node_or_error(info, id, only_type=User)
        cls.clean_instance(info, instance)

        db_id = instance.id
        remove_staff_member(instance)
        # After the instance is deleted, set its ID to the original database's
        # ID so that the success response contains ID of the deleted object.
        instance.id = db_id

        response = cls.success_response(instance)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.staff_deleted, instance)

        return response


class AddressCreate(ModelMutation):
    user = graphene.Field(
        User, description="A user instance for which the address was created."
    )

    class Arguments:
        user_id = graphene.ID(
            description="ID of a user to create address for.", required=True
        )
        input = AddressInput(
            description="Fields required to create address.", required=True
        )

    class Meta:
        description = "Creates user address."
        model = models.Address
        object_type = Address
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        user_id = data["user_id"]
        user = cls.get_node_or_error(info, user_id, field="user_id", only_type=User)
        with traced_atomic_transaction():
            response = super().perform_mutation(root, info, **data)
            if not response.errors:
                manager = get_plugin_manager_promise(info.context).get()
                address = manager.change_user_address(response.address, None, user)
                remove_the_oldest_user_address_if_address_limit_is_reached(user)
                user.addresses.add(address)
                response.user = user
                user.search_document = prepare_user_search_document_value(user)
                user.save(update_fields=["search_document", "updated_at"])
            return response

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.address_created, instance)


class AddressUpdate(BaseAddressUpdate):
    class Meta:
        description = "Updates an address."
        model = models.Address
        object_type = Address
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"


class AddressDelete(BaseAddressDelete):
    class Meta:
        description = "Deletes an address."
        model = models.Address
        object_type = Address
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"


class AddressSetDefault(BaseMutation):
    user = graphene.Field(User, description="An updated user instance.")

    class Arguments:
        address_id = graphene.ID(required=True, description="ID of the address.")
        user_id = graphene.ID(
            required=True, description="ID of the user to change the address for."
        )
        type = AddressTypeEnum(required=True, description="The type of address.")

    class Meta:
        description = "Sets a default address for the given user."
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, address_id, user_id, type
    ):
        address = cls.get_node_or_error(
            info, address_id, field="address_id", only_type=Address
        )
        user = cls.get_node_or_error(info, user_id, field="user_id", only_type=User)

        if not user.addresses.filter(pk=address.pk).exists():
            raise ValidationError(
                {
                    "address_id": ValidationError(
                        "The address doesn't belong to that user.",
                        code=AccountErrorCode.INVALID.value,
                    )
                }
            )

        if type == AddressTypeEnum.BILLING.value:
            address_type = AddressType.BILLING
        else:
            address_type = AddressType.SHIPPING
        manager = get_plugin_manager_promise(info.context).get()
        utils.change_user_default_address(user, address, address_type, manager)
        cls.call_event(manager.customer_updated, user)
        return cls(user=user)


class UserAvatarUpdate(BaseMutation):
    user = graphene.Field(User, description="An updated user instance.")

    class Arguments:
        image = Upload(
            required=True,
            description="Represents an image file in a multipart request.",
        )

    class Meta:
        description = (
            "Create a user avatar. Only for staff members. This mutation must be sent "
            "as a `multipart` request. More detailed specs of the upload format can be "
            "found here: https://github.com/jaydenseric/graphql-multipart-request-spec"
        )
        error_type_class = AccountError
        error_type_field = "account_errors"
        permissions = (AuthorizationFilters.AUTHENTICATED_STAFF_USER,)

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        user = info.context.user
        user = cast(models.User, user)
        data["image"] = info.context.FILES.get(data["image"])
        image_data = clean_image_file(data, "image", AccountErrorCode)
        if user.avatar:
            user.avatar.delete()
            thumbnail_models.Thumbnail.objects.filter(user_id=user.id).delete()
        user.avatar = image_data
        user.save()

        return UserAvatarUpdate(user=user)


class UserAvatarDelete(BaseMutation):
    user = graphene.Field(User, description="An updated user instance.")

    class Meta:
        description = "Deletes a user avatar. Only for staff members."
        error_type_class = AccountError
        error_type_field = "account_errors"
        permissions = (AuthorizationFilters.AUTHENTICATED_STAFF_USER,)

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /):
        user = info.context.user
        user = cast(models.User, user)
        user.avatar.delete()
        thumbnail_models.Thumbnail.objects.filter(user_id=user.id).delete()
        return UserAvatarDelete(user=user)

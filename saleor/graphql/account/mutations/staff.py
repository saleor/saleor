from collections import defaultdict
from copy import copy

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction
from graphql_jwt.decorators import staff_member_required
from graphql_jwt.exceptions import PermissionDenied

from ....account import events as account_events, models, utils
from ....account.emails import send_set_password_email_with_url
from ....account.error_codes import AccountErrorCode
from ....account.thumbnails import create_user_avatar_thumbnails
from ....account.utils import remove_staff_member
from ....checkout import AddressType
from ....core.permissions import AccountPermissions
from ....core.utils.url import validate_storefront_url
from ...account.enums import AddressTypeEnum
from ...account.types import Address, AddressInput, User
from ...core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ...core.types import Upload
from ...core.types.common import AccountError, StaffError
from ...core.utils import get_duplicates_ids, validate_image_file
from ...meta.deprecated.mutations import ClearMetaBaseMutation, UpdateMetaBaseMutation
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
    add_groups = graphene.List(
        graphene.NonNull(graphene.ID),
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
    remove_groups = graphene.List(
        graphene.NonNull(graphene.ID),
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
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"


class CustomerUpdate(CustomerCreate):
    class Arguments:
        id = graphene.ID(description="ID of a customer to update.", required=True)
        input = CustomerInput(
            description="Fields required to update a customer.", required=True
        )

    class Meta:
        description = "Updates an existing customer."
        exclude = ["password"]
        model = models.User
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def generate_events(
        cls, info, old_instance: models.User, new_instance: models.User
    ):
        # Retrieve the event base data
        staff_user = info.context.user
        new_email = new_instance.email
        new_fullname = new_instance.get_full_name()

        # Compare the data
        has_new_name = old_instance.get_full_name() != new_fullname
        has_new_email = old_instance.email != new_email

        # Generate the events accordingly
        if has_new_email:
            account_events.staff_user_assigned_email_to_a_customer_event(
                staff_user=staff_user, new_email=new_email
            )
        if has_new_name:
            account_events.staff_user_assigned_name_to_a_customer_event(
                staff_user=staff_user, new_name=new_fullname
            )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
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


class UserDelete(UserDeleteMixin, ModelDeleteMutation):
    class Meta:
        abstract = True


class CustomerDelete(CustomerDeleteMixin, UserDelete):
    class Meta:
        description = "Deletes a customer."
        model = models.User
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    class Arguments:
        id = graphene.ID(required=True, description="ID of a customer to delete.")

    @classmethod
    def perform_mutation(cls, root, info, **data):
        results = super().perform_mutation(root, info, **data)
        cls.post_process(info)
        return results


class StaffCreate(ModelMutation):
    class Arguments:
        input = StaffCreateInput(
            description="Fields required to create a staff user.", required=True
        )

    class Meta:
        description = "Creates a new staff user."
        exclude = ["password"]
        model = models.User
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = StaffError
        error_type_field = "staff_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)

        errors = defaultdict(list)
        if cleaned_input.get("redirect_url"):
            try:
                validate_storefront_url(cleaned_input.get("redirect_url"))
            except ValidationError as error:
                error.code = AccountErrorCode.INVALID
                errors["redirect_url"].append(error)

        requestor = info.context.user
        # set is_staff to True to create a staff user
        cleaned_input["is_staff"] = True
        cls.clean_groups(requestor, cleaned_input, errors)
        cls.clean_is_active(cleaned_input, instance, info.context.user, errors)

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
    def save(cls, info, user, cleaned_input):
        user.save()
        if cleaned_input.get("redirect_url"):
            send_set_password_email_with_url(
                redirect_url=cleaned_input.get("redirect_url"), user=user, staff=True
            )

    @classmethod
    @transaction.atomic
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        groups = cleaned_data.get("add_groups")
        if groups:
            instance.groups.add(*groups)


class StaffUpdate(StaffCreate):
    class Arguments:
        id = graphene.ID(description="ID of a staff user to update.", required=True)
        input = StaffUpdateInput(
            description="Fields required to update a staff user.", required=True
        )

    class Meta:
        description = "Updates an existing staff user."
        exclude = ["password"]
        model = models.User
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = StaffError
        error_type_field = "staff_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        requestor = info.context.user
        # check if requestor can manage this user
        if not requestor.is_superuser and get_out_of_scope_users(requestor, [instance]):
            msg = "You can't manage this user."
            code = AccountErrorCode.OUT_OF_SCOPE_USER.value
            raise ValidationError({"id": ValidationError(msg, code=code)})

        cls.check_for_duplicates(data)

        cleaned_input = super().clean_input(info, instance, data)

        return cleaned_input

    @classmethod
    def check_for_duplicates(cls, input_data):
        duplicated_ids = get_duplicates_ids(
            input_data.get("add_groups"), input_data.get("remove_groups")
        )
        if duplicated_ids:
            # add error
            msg = (
                "The same object cannot be in both list"
                "for adding and removing items."
            )
            code = AccountErrorCode.DUPLICATED_INPUT_ITEM.value
            params = {"groups": duplicated_ids}
            raise ValidationError(msg, code=code, params=params)

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
            user: requestor

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
    @transaction.atomic
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        add_groups = cleaned_data.get("add_groups")
        if add_groups:
            instance.groups.add(*add_groups)
        remove_groups = cleaned_data.get("remove_groups")
        if remove_groups:
            instance.groups.remove(*remove_groups)


class StaffDelete(StaffDeleteMixin, UserDelete):
    class Meta:
        description = "Deletes a staff user."
        model = models.User
        permissions = (AccountPermissions.MANAGE_STAFF,)
        error_type_class = StaffError
        error_type_field = "staff_errors"

    class Arguments:
        id = graphene.ID(required=True, description="ID of a staff user to delete.")

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        if not cls.check_permissions(info.context):
            raise PermissionDenied()

        user_id = data.get("id")
        instance = cls.get_node_or_error(info, user_id, only_type=User)
        cls.clean_instance(info, instance)

        db_id = instance.id
        remove_staff_member(instance)
        # After the instance is deleted, set its ID to the original database's
        # ID so that the success response contains ID of the deleted object.
        instance.id = db_id
        return cls.success_response(instance)


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
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        user_id = data["user_id"]
        user = cls.get_node_or_error(info, user_id, field="user_id", only_type=User)
        response = super().perform_mutation(root, info, **data)
        if not response.errors:
            address = info.context.plugins.change_user_address(
                response.address, None, user
            )
            user.addresses.add(address)
            response.user = user
        return response


class AddressUpdate(BaseAddressUpdate):
    class Meta:
        description = "Updates an address."
        model = models.Address
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"


class AddressDelete(BaseAddressDelete):
    class Meta:
        description = "Deletes an address."
        model = models.Address
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
    def perform_mutation(cls, _root, info, address_id, user_id, **data):
        address = cls.get_node_or_error(
            info, address_id, field="address_id", only_type=Address
        )
        user = cls.get_node_or_error(info, user_id, field="user_id", only_type=User)

        if not user.addresses.filter(pk=address.pk).exists():
            raise ValidationError(
                {
                    "address_id": ValidationError(
                        "The address doesn't belong to that user.",
                        code=AccountErrorCode.INVALID,
                    )
                }
            )

        if data.get("type") == AddressTypeEnum.BILLING.value:
            address_type = AddressType.BILLING
        else:
            address_type = AddressType.SHIPPING

        utils.change_user_default_address(user, address, address_type)
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

    @classmethod
    @staff_member_required
    def perform_mutation(cls, _root, info, image):
        user = info.context.user
        image_data = info.context.FILES.get(image)
        validate_image_file(image_data, "image")

        if user.avatar:
            user.avatar.delete_sized_images()
            user.avatar.delete()
        user.avatar = image_data
        user.save()
        create_user_avatar_thumbnails.delay(user_id=user.pk)

        return UserAvatarUpdate(user=user)


class UserAvatarDelete(BaseMutation):
    user = graphene.Field(User, description="An updated user instance.")

    class Meta:
        description = "Deletes a user avatar. Only for staff members."
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    @staff_member_required
    def perform_mutation(cls, _root, info):
        user = info.context.user
        user.avatar.delete_sized_images()
        user.avatar.delete()
        return UserAvatarDelete(user=user)


class UserUpdatePrivateMeta(UpdateMetaBaseMutation):
    class Meta:
        description = "Updates private metadata for user."
        permissions = (AccountPermissions.MANAGE_USERS,)
        model = models.User
        public = False
        error_type_class = AccountError
        error_type_field = "account_errors"


class UserClearPrivateMeta(ClearMetaBaseMutation):
    class Meta:
        description = "Clear private metadata for user."
        model = models.User
        permissions = (AccountPermissions.MANAGE_USERS,)
        public = False
        error_type_class = AccountError
        error_type_field = "account_errors"

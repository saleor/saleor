from copy import copy

import graphene
from django.core.exceptions import ValidationError
from graphql_jwt.decorators import staff_member_required
from graphql_jwt.exceptions import PermissionDenied

from ....account import events as account_events, models, utils
from ....account.thumbnails import create_user_avatar_thumbnails
from ....account.utils import get_random_avatar
from ....checkout import AddressType
from ....core.permissions import get_permissions
from ....dashboard.emails import (
    send_set_password_customer_email,
    send_set_password_staff_email,
)
from ....dashboard.staff.utils import remove_staff_member
from ...account.enums import AddressTypeEnum
from ...account.i18n import I18nMixin
from ...account.types import Address, AddressInput, User
from ...core.enums import PermissionEnum
from ...core.mutations import (
    BaseMutation,
    ClearMetaBaseMutation,
    ModelDeleteMutation,
    ModelMutation,
    UpdateMetaBaseMutation,
)
from ...core.types import Upload
from ...core.utils import validate_image_file
from ..utils import CustomerDeleteMixin, StaffDeleteMixin, UserDeleteMixin
from .base import BaseAddressUpdate

BILLING_ADDRESS_FIELD = "default_billing_address"
SHIPPING_ADDRESS_FIELD = "default_shipping_address"


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


class StaffInput(UserInput):
    permissions = graphene.List(
        PermissionEnum,
        description="List of permission code names to assign to this user.",
    )


class StaffCreateInput(StaffInput):
    send_password_email = graphene.Boolean(
        description="Send an email with a link to set a password"
    )


class CustomerCreate(ModelMutation, I18nMixin):
    class Arguments:
        input = UserCreateInput(
            description="Fields required to create a customer.", required=True
        )

    class Meta:
        description = "Creates a new customer."
        exclude = ["password"]
        model = models.User
        permissions = ("account.manage_users",)

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
        permissions = ("account.manage_users",)

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
        cls.clean_instance(new_instance)
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
        permissions = ("account.manage_users",)

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
        permissions = ("account.manage_staff",)

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)

        # set is_staff to True to create a staff user
        cleaned_input["is_staff"] = True

        # clean and prepare permissions
        if "permissions" in cleaned_input:
            permissions = cleaned_input.pop("permissions")
            cleaned_input["user_permissions"] = get_permissions(permissions)
        return cleaned_input

    @classmethod
    def save(cls, info, user, cleaned_input):
        create_avatar = not user.avatar
        if create_avatar:
            user.avatar = get_random_avatar()
        user.save()
        if create_avatar:
            create_user_avatar_thumbnails.delay(user_id=user.pk)
        if cleaned_input.get("send_password_email"):
            send_set_password_staff_email.delay(user.pk)


class StaffUpdate(StaffCreate):
    class Arguments:
        id = graphene.ID(description="ID of a staff user to update.", required=True)
        input = StaffInput(
            description="Fields required to update a staff user.", required=True
        )

    class Meta:
        description = "Updates an existing staff user."
        exclude = ["password"]
        model = models.User
        permissions = ("account.manage_staff",)

    @classmethod
    def clean_is_active(cls, is_active, instance, user):
        if not is_active:
            if user == instance:
                raise ValidationError(
                    {"is_active": "Cannot deactivate your own account."}
                )
            elif instance.is_superuser:
                raise ValidationError(
                    {"is_active": "Cannot deactivate superuser's account."}
                )

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        is_active = cleaned_input.get("is_active")
        if is_active is not None:
            cls.clean_is_active(is_active, instance, info.context.user)
        return cleaned_input


class StaffDelete(StaffDeleteMixin, UserDelete):
    class Meta:
        description = "Deletes a staff user."
        model = models.User
        permissions = ("account.manage_staff",)

    class Arguments:
        id = graphene.ID(required=True, description="ID of a staff user to delete.")

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        if not cls.check_permissions(info.context.user):
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
            description="ID of a user to create address for", required=True
        )
        input = AddressInput(
            description="Fields required to create address", required=True
        )

    class Meta:
        description = "Creates user address"
        model = models.Address
        permissions = ("account.manage_users",)

    @classmethod
    def perform_mutation(cls, root, info, **data):
        user_id = data["user_id"]
        user = cls.get_node_or_error(info, user_id, field="user_id", only_type=User)
        response = super().perform_mutation(root, info, **data)
        if not response.errors:
            user.addresses.add(response.address)
            response.user = user
        return response


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
        permissions = ("account.manage_users",)

    @classmethod
    def perform_mutation(cls, _root, info, address_id, user_id, **data):
        address = cls.get_node_or_error(
            info, address_id, field="address_id", only_type=Address
        )
        user = cls.get_node_or_error(info, user_id, field="user_id", only_type=User)

        if address not in user.addresses.all():
            raise ValidationError(
                {"address_id": "The address doesn't belong to that user."}
            )

        if data.get("type") == AddressTypeEnum.BILLING.value:
            address_type = AddressType.BILLING
        else:
            address_type = AddressType.SHIPPING

        utils.change_user_default_address(user, address, address_type)
        return cls(user=user)


class AddressUpdate(BaseAddressUpdate):
    class Meta:
        permissions = ("account.manage_users",)
        description = "Updates an address"
        model = models.Address
        exclude = ["user_addresses"]


class UserAvatarUpdate(BaseMutation):
    user = graphene.Field(User, description="An updated user instance.")

    class Arguments:
        image = Upload(
            required=True,
            description="Represents an image file in a multipart request.",
        )

    class Meta:
        description = """
            Create a user avatar. Only for staff members. This mutation must
            be sent as a `multipart` request. More detailed specs of the
            upload format can be found here:
            https://github.com/jaydenseric/graphql-multipart-request-spec
            """

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
        permissions = ("account.manage_users",)
        model = models.User
        public = False


class UserClearStoredPrivateMeta(ClearMetaBaseMutation):
    class Meta:
        description = "Clear stored metadata value."
        model = models.User
        permissions = ("account.manage_users",)
        public = False

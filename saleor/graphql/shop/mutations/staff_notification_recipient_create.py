import graphene
from django.core.exceptions import ValidationError

from ....account import models as account_models
from ....core.error_codes import ShopErrorCode
from ....permission.enums import SitePermissions
from ...account.types import StaffNotificationRecipient
from ...core.mutations import ModelMutation
from ...core.types import ShopError


class StaffNotificationRecipientInput(graphene.InputObjectType):
    user = graphene.ID(
        required=False,
        description="The ID of the user subscribed to email notifications..",
    )
    email = graphene.String(
        required=False,
        description="Email address of a user subscribed to email notifications.",
    )
    active = graphene.Boolean(
        required=False, description="Determines if a notification active."
    )


class StaffNotificationRecipientCreate(ModelMutation):
    class Arguments:
        input = StaffNotificationRecipientInput(
            required=True,
            description="Fields required to create a staff notification recipient.",
        )

    class Meta:
        description = "Creates a new staff notification recipient."
        model = account_models.StaffNotificationRecipient
        object_type = StaffNotificationRecipient
        permissions = (SitePermissions.MANAGE_SETTINGS,)
        error_type_class = ShopError
        error_type_field = "shop_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        cls.validate_input(instance, cleaned_input)
        email = cleaned_input.pop("email", None)
        if email:
            staff_user = account_models.User.objects.filter(email=email).first()
            if staff_user:
                cleaned_input["user"] = staff_user
            else:
                cleaned_input["staff_email"] = email
        return cleaned_input

    @staticmethod
    def validate_input(instance, cleaned_input):
        email = cleaned_input.get("email")
        user = cleaned_input.get("user")
        if not email and not user:
            if instance.id and "user" in cleaned_input or "email" in cleaned_input:
                raise ValidationError(
                    {
                        "staff_notification": ValidationError(
                            "User and email cannot be set empty",
                            code=ShopErrorCode.INVALID.value,
                        )
                    }
                )
            if not instance.id:
                raise ValidationError(
                    {
                        "staff_notification": ValidationError(
                            "User or email is required",
                            code=ShopErrorCode.REQUIRED.value,
                        )
                    }
                )
        if user and not user.is_staff:
            raise ValidationError(
                {
                    "user": ValidationError(
                        "User has to be staff user", code=ShopErrorCode.INVALID.value
                    )
                }
            )

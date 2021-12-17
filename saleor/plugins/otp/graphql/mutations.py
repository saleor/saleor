from datetime import timedelta
from typing import Optional

import graphene
from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils import timezone

from ....account import events as account_events
from ....account.error_codes import AccountErrorCode
from ....account.notifications import get_default_user_payload
from ....core.notification.utils import get_site_context
from ....core.notify_events import NotifyEventType
from ....graphql.account.mutations.authentication import CreateToken
from ....graphql.channel.utils import clean_channel, validate_channel
from ....graphql.core.mutations import BaseMutation, validation_error_to_error_type
from ....graphql.core.types.common import AccountError
from ..models import OTP

User = get_user_model()


def send_password_reset_notification(
    user, manager, channel_slug: Optional[str], staff=False
):

    otp = OTP.objects.create(user=user)

    payload = {
        "user": get_default_user_payload(user),
        "recipient_email": user.email,
        "token": str(otp),
        "channel_slug": channel_slug,
        **get_site_context(),
    }

    event = (
        NotifyEventType.ACCOUNT_STAFF_RESET_PASSWORD
        if staff
        else NotifyEventType.ACCOUNT_PASSWORD_RESET
    )
    manager.notify(event, payload=payload, channel_slug=channel_slug)


class RequestPasswordRecovery(BaseMutation):
    class Arguments:
        email = graphene.String(
            required=True,
            description="Email of the user that will be used for password recovery.",
        )
        channel = graphene.String(
            description=(
                "Slug of a channel which will be used for notify user. Optional when "
                "only one channel exists."
            )
        )

    class Meta:
        description = "Sends an email with the account password modification link."
        error_type_class = AccountError
        error_type_field = "account_errors"

    def clean_user(email):
        try:
            return User.objects.get(email=email)
        except ObjectDoesNotExist:
            raise ValidationError(
                {
                    "email": ValidationError(
                        "User with this email doesn't exist",
                        code=AccountErrorCode.NOT_FOUND,
                    )
                }
            )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        email = data["email"]
        channel_slug = data.get("channel")
        user = cls.clean_user(email)

        if not user.is_staff:
            channel_slug = clean_channel(
                channel_slug, error_class=AccountErrorCode
            ).slug
        elif channel_slug is not None:
            channel_slug = validate_channel(
                channel_slug, error_class=AccountErrorCode
            ).slug

        send_password_reset_notification(
            user,
            info.context.plugins,
            channel_slug=channel_slug,
            staff=user.is_staff,
        )
        return RequestPasswordRecovery()


class SetPasswordByCode(CreateToken):
    class Arguments:
        code = graphene.String(
            description="An OTP required to set the password.", required=True
        )
        email = graphene.String(required=True, description="Email of a user.")
        password = graphene.String(required=True, description="Password of a user.")

    class Meta:
        description = (
            "Sets the user's password from the token sent by email "
            "using the RequestPasswordReset mutation."
        )
        error_type_class = AccountError  # have custom OTP error
        error_type_field = "account_errors"

    @classmethod
    def fail(cls, message):
        raise ValidationError(message, code=AccountErrorCode.INVALID)

    @classmethod
    def handle_used_otp(cls, otp: OTP):
        if otp.is_used:
            cls.fail("Used OTP supplied")

    @classmethod
    def handle_expired_otp(cls, otp: OTP):
        if otp.issued_at + timedelta(minutes=15) <= timezone.now():
            cls.fail("Invalid OTP supplied")

    @classmethod
    def _set_password_for_user(cls, email, password, code):
        try:
            user = User.objects.get(email=email)
        except ObjectDoesNotExist:
            raise ValidationError(
                {
                    "email": ValidationError(
                        "User doesn't exist", code=AccountErrorCode.NOT_FOUND
                    )
                }
            )

        try:
            otp = OTP.objects.get(code=code, user=user)
        except OTP.DoesNotExist:
            cls.fail("Invalid OTP supplied")

        cls.handle_used_otp(otp)
        cls.handle_expired_otp(otp)

        try:
            password_validation.validate_password(password, user)
        except ValidationError as error:
            raise ValidationError({"password": error})

        user.set_password(password)
        user.save(update_fields=["password"])
        account_events.customer_password_reset_event(user=user)

    @classmethod
    def perform_mutation(cls, root, info, **data):
        email = data["email"]
        password = data["password"]
        code = data["code"]

        try:
            cls._set_password_for_user(email, password, code)
        except ValidationError as e:
            errors = validation_error_to_error_type(e, AccountError)
            return cls.handle_typed_errors(errors)
        return super().perform_mutation(root, info, **data)

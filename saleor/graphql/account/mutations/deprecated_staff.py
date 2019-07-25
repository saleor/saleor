import graphene
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from ....account import models
from ...core.mutations import BaseMutation
from .base import send_user_password_reset_email


class PasswordReset(BaseMutation):
    class Arguments:
        email = graphene.String(description="Email", required=True)

    class Meta:
        description = (
            "DEPRECATED: Use CustomerRequestPasswordReset instead."
            "Sends an email with the account password change link to customer."
        )
        permissions = ("account.manage_users",)

    @classmethod
    def perform_mutation(cls, _root, info, email):
        try:
            user = models.User.objects.get(email=email)
        except ObjectDoesNotExist:
            raise ValidationError({"email": "User with this email doesn't exist"})
        site = info.context.site
        send_user_password_reset_email(user, site)
        return PasswordReset()

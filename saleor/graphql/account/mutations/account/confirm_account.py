import logging

import graphene
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from .....account import models
from .....account.error_codes import AccountErrorCode
from .....account.throttling import authenticate_with_throttling
from .....core.tokens import (
    account_confirm_token_generator,
    legacy_account_confirm_token_generator,
    try_generators,
)
from .....giftcard.utils import assign_user_gift_cards
from .....order.utils import match_orders_with_new_user
from .....webhook.event_types import WebhookEventAsyncType
from ....core import ResolveInfo, SaleorContext
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import BaseMutation
from ....core.types import AccountError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import User

INVALID_TOKEN = "Invalid or expired token."


logger = logging.getLogger(__name__)


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
        password = graphene.String(
            required=True,
            description="Password of the user confirming their account.",
        )

    class Meta:
        description = (
            "Confirm user account with token sent by email during registration."
        )
        doc_category = DOC_CATEGORY_USERS
        error_type_class = AccountError
        error_type_field = "account_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.ACCOUNT_CONFIRMED,
                description="Account was confirmed.",
            ),
        ]

    @staticmethod
    def merge_account(
        *,
        request: SaleorContext,
        user: models.User,
        password: str,
    ) -> None:
        """Merge the account if the user confirms their knowledge of the password.

        Note: having different response times and different error messages
              which would reveal the user's existence is not a security issue
              in this context. We already verified the user has the account
              confirmation token. We are only verifying whether they know the
              password of that account and thus we're trying to ensure they
              aren't being tricked by someone.
        """

        auth_user = authenticate_with_throttling(
            request=request,
            email=user.email,
            password=password,
        )

        if not auth_user or auth_user != user:
            # This should be impossible, but if it occurs, then don't crash, just
            # log a fatal error so someone can look into and just return "Invalid password"
            # to the user
            # Note: auth_user can be null if the password is wrong, in which case we
            #       shouldn't throw an error in logs
            if auth_user is not None and auth_user != user:
                logger.exception(
                    "Unexpected user mismatch during authentication in"
                    " confirmAccount() mutation"
                )

            raise ValidationError(
                {
                    "password": ValidationError(
                        "Invalid password", code=AccountErrorCode.INVALID.value
                    )
                }
            )

        # User proved they possess their password, thus it's safe to merge
        match_orders_with_new_user(user)
        assign_user_gift_cards(user)

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        error = False
        try:
            user = models.User.objects.get(
                email=data["email"], is_active=True, is_confirmed=False
            )
        except ObjectDoesNotExist:
            # If user doesn't exists in the database we create fake user for calculation
            # purpose, as we don't want to indicate non existence of user in the system.
            error = True
            user = models.User()

        valid_token = try_generators(
            current_generator=account_confirm_token_generator,
            fallback_generator=legacy_account_confirm_token_generator,
            user=user,
            token=data["token"],
        )
        if not valid_token or error:
            raise ValidationError(
                {
                    "token": ValidationError(
                        INVALID_TOKEN, code=AccountErrorCode.INVALID.value
                    )
                }
            )

        cls.merge_account(
            request=info.context,
            user=user,
            password=data["password"],
        )

        user.is_active = True
        user.is_confirmed = True
        user.save(update_fields=["is_confirmed", "updated_at"])

        cls.post_save_action(info, user)

        return ConfirmAccount(user=user)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.account_confirmed, instance)

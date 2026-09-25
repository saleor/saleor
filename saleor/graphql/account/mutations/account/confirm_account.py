import logging
from typing import Any

import graphene
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from .....account import models
from .....account.error_codes import AccountErrorCode
from .....account.throttling import authenticate_with_throttling
from .....core.tokens import (
    account_confirm_token_generator,
)
from .....giftcard.utils import assign_user_gift_cards
from .....order.utils import match_orders_with_new_user
from .....site import AccountConfirmMode
from .....site.models import SiteSettings
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
            description=(
                "Password of the user confirming their account. Required "
                "when `REQUIRED_PASSWORD` mode is enabled in shop settings. "
                "Learn more at "
                "https://docs.saleor.io/upgrade-guides/core/migrate-account-merging"
            )
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
    def maybe_merge_account(
        *,
        request: SaleorContext,
        user: models.User,
        site_settings: SiteSettings,
        data: dict[str, Any],
    ) -> None:
        """Merge the account if the user confirms their knowledge of the password.

        Note: having different response times and different error messages
              which would reveal the user's existence is not a security issue
              in this context. We already verified the user has the account
              confirmation token. We are only verifying whether they know the
              password of that account and thus we're trying to ensure they
              aren't being tricked by someone.
        """
        if (
            site_settings.account_confirm_merge_mode
            == AccountConfirmMode.MERGE_DISABLED
        ):
            return

        if (
            site_settings.account_confirm_merge_mode
            != AccountConfirmMode.REQUIRE_PASSWORD
        ):
            raise ValueError(
                "Received an unknown account merging mode",
                site_settings.account_confirm_merge_mode,
            )

        password: str | None = data.get("password")

        # development safeguard due to Graphene automatically casting non-string
        # to strings
        assert password is None or isinstance(password, str)

        if not password:
            raise ValidationError(
                {
                    "password": ValidationError(
                        "Password is required", code=AccountErrorCode.REQUIRED.value
                    )
                }
            )

        auth_user = authenticate_with_throttling(
            request=request, email=user.email, password=password
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

        valid_token = account_confirm_token_generator.check_token(
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

        cls.maybe_merge_account(
            request=info.context,
            user=user,
            # Note: doesn't use Site.objects.get_current().settings as it will
            # retrieve stale data (in-memory cache)
            site_settings=SiteSettings.objects.get(site=Site.objects.get_current()),
            data=data,
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

from typing import TYPE_CHECKING, Optional

from django.core.exceptions import ValidationError

from ...page.models import PageType
from ...payment import models as payment_models

if TYPE_CHECKING:
    from ...account.models import User
    from ...app.models import App


def deprecated_metadata_contains_empty_key(metadata_list: list[dict]) -> bool:
    """Check if metadata list contains empty key.

    Deprecated.
    Construct MetadataItemCollection instead, that internally validates metadata structure.
    """
    return not all(data["key"].strip() for data in metadata_list)


def check_if_requestor_has_access(
    transaction: payment_models.TransactionItem,
    user: Optional["User"],
    app: Optional["App"],
):
    # Previously we didn't require app/user attached to transaction. We can't
    # determine which app/user is an owner of the transaction. So for transaction
    # without attached owner we require only HANDLE_PAYMENTS.
    if (
        not transaction.user_id
        and not transaction.app_identifier
        and not transaction.app_id
    ):
        return True

    if user and transaction.user_id:
        return True

    if app:
        if transaction.app_id == app.id:
            return True

        if transaction.app_identifier and transaction.app_identifier == app.identifier:
            return True
    return False


def validate_reason_reference_context(
    *,
    reason_reference_id: str | None,
    requestor_is_user: bool,
    reason_reference_field_name: str,
    error_code_enum,
    reason_reference_type: PageType | None,
) -> bool:
    """Validate conditions for applying reason reference.

    This does not verify that ``reason_reference_id`` points to a Page of
    ``reason_reference_type``.

    The caller must supply ``reason_reference_type`` (e.g. the refund or return
    reason reference type from the site settings); passing ``None`` means no
    reference type is configured.

    Returns ``should_apply`` — whether a reason reference should be resolved and
    applied. When it is ``True`` the supplied ``reason_reference_type`` is
    guaranteed to be set, so the caller can resolve against it directly.
    """
    if not reason_reference_type and reason_reference_id:
        raise ValidationError(
            {
                reason_reference_field_name: ValidationError(
                    "Reason reference type is not configured.",
                    code=error_code_enum.INVALID.value,
                )
            }
        ) from None

    if (
        reason_reference_type is not None
        and reason_reference_id is None
        and requestor_is_user
    ):
        raise ValidationError(
            {
                reason_reference_field_name: ValidationError(
                    "Reason reference is required when reason reference type is configured.",
                    code=error_code_enum.REQUIRED.value,
                )
            }
        ) from None

    return bool(reason_reference_id is not None and reason_reference_type)

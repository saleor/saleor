from typing import TYPE_CHECKING, Any, Optional

from django.core.exceptions import ValidationError

from ...page.models import PageType
from ...payment import models as payment_models
from ...site.models import SiteSettings

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


# Sentinel for ``validate_and_resolve_refund_reason_context``: when no explicit
# reference type is passed, fall back to the refund reason reference type from the
# site settings. Passing ``None`` explicitly means the reference type is not
# configured (e.g. for return reasons that have not been set up).
_USE_REFUND_REASON_REFERENCE_TYPE: Any = object()


def validate_and_resolve_refund_reason_context(
    *,
    reason_reference_id: str | None,
    requestor_is_user: bool,
    refund_reference_field_name: str,
    error_code_enum,
    site_settings: SiteSettings,
    reason_reference_type: PageType | None = _USE_REFUND_REASON_REFERENCE_TYPE,
) -> tuple[bool, PageType | None]:
    """Validate a reason reference against the configured reference type.

    By default the refund reason reference type from the site settings is used.
    Pass ``reason_reference_type`` explicitly (e.g. the return reason reference
    type) to validate against another configured type; passing ``None`` means no
    reference type is configured.
    """
    if reason_reference_type is _USE_REFUND_REASON_REFERENCE_TYPE:
        reason_reference_type = site_settings.refund_reason_reference_type

    if not reason_reference_type and reason_reference_id:
        raise ValidationError(
            {
                refund_reference_field_name: ValidationError(
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
                refund_reference_field_name: ValidationError(
                    "Reason reference is required when reason reference type is configured.",
                    code=error_code_enum.REQUIRED.value,
                )
            }
        ) from None

    should_apply = bool(reason_reference_id is not None and reason_reference_type)

    return should_apply, reason_reference_type

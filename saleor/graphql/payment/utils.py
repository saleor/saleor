from typing import TYPE_CHECKING, Optional

from django.core.exceptions import ValidationError
from graphql import GraphQLError

from ...page.models import Page
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


def validate_and_resolve_refund_reason_context(
    *,
    reason_reference_id: str | None,
    requestor_is_user: bool,
    refund_reference_field_name: str,
    error_code_enum,
    site_settings: SiteSettings,
):
    refund_reason_reference_type = site_settings.refund_reason_reference_type

    is_passing_reason_reference_required: bool = (
        refund_reason_reference_type is not None
    )

    if not refund_reason_reference_type and reason_reference_id:
        raise ValidationError(
            {
                refund_reference_field_name: ValidationError(
                    "Reason reference type is not configured.",
                    code=error_code_enum.GRAPHQL_ERROR.value,
                )
            }
        ) from None

    if (
        is_passing_reason_reference_required
        and reason_reference_id is None
        and requestor_is_user
    ):
        raise ValidationError(
            {
                refund_reference_field_name: ValidationError(
                    "Reason reference is required when refund reason reference type is configured.",
                    code=error_code_enum.REQUIRED.value,
                )
            }
        ) from None

    should_apply = bool(
        reason_reference_id is not None and refund_reason_reference_type
    )

    return {
        "is_passing_reason_reference_required": is_passing_reason_reference_required,
        "refund_reason_reference_type": refund_reason_reference_type,
        "should_apply": should_apply,
    }


def validate_per_line_reason_reference(
    *,
    reason_reference_id: str | None,
    site_settings: SiteSettings,
    error_code_enum,
    field_name: str = "reason_reference",
):
    """Validate per-line reason reference.

    Per-line reason references are always optional (for both staff and apps),
    but when provided the referenced Page must match the configured PageType.
    """
    refund_reason_reference_type = site_settings.refund_reason_reference_type

    if not refund_reason_reference_type and reason_reference_id:
        raise ValidationError(
            {
                field_name: ValidationError(
                    "Reason reference type is not configured.",
                    code=error_code_enum.GRAPHQL_ERROR.value,
                )
            }
        ) from None

    should_apply = bool(
        reason_reference_id is not None and refund_reason_reference_type
    )

    return {
        "refund_reason_reference_type": refund_reason_reference_type,
        "should_apply": should_apply,
    }


def resolve_reason_reference_page(
    reason_reference_id: str,
    refund_reason_reference_type_id: int,
    error_code_enum,
    *,
    field_name: str = "reason_reference",
) -> Page:
    """Resolve and validate a reason reference Page by global ID and PageType.

    The referenced Page must belong to the PageType configured in
    refundReasonReferenceType site setting.
    """
    from ..core.utils import from_global_id_or_error

    try:
        _, reason_reference_pk = from_global_id_or_error(
            reason_reference_id, only_type="Page", raise_error=True
        )
    except GraphQLError:
        raise ValidationError(
            {
                field_name: ValidationError(
                    "Invalid reason reference. Must be an ID of a Page with the "
                    "configured PageType.",
                    code=error_code_enum.GRAPHQL_ERROR.value,
                )
            }
        ) from None
    try:
        return Page.objects.get(
            pk=reason_reference_pk,
            page_type=refund_reason_reference_type_id,
        )
    except Page.DoesNotExist:
        raise ValidationError(
            {
                field_name: ValidationError(
                    "Invalid reason reference. Must be an ID of a Page with the "
                    "configured PageType.",
                    code=error_code_enum.INVALID.value,
                )
            }
        ) from None

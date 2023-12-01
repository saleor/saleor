from typing import TYPE_CHECKING, Optional

from ...payment import models as payment_models

if TYPE_CHECKING:
    from ...account.models import User
    from ...app.models import App


def metadata_contains_empty_key(metadata_list: list[dict]) -> bool:
    return not all([data["key"].strip() for data in metadata_list])


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

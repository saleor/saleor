from ...account import models
from ...account.error_codes import AccountErrorCode
from ...app.models import App
from ...core.exceptions import PermissionDenied
from ...core.utils import metadata_manager
from ...permission.enums import AccountPermissions
from ..core.utils import raise_validation_error
from ..meta.inputs import MetadataInput
from ..utils import get_user_or_app_from_context


class AddressMetadataMixin:
    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        metadata: list[MetadataInput] = cleaned_data.pop("metadata", [])

        metadata_collection = super().create_metadata_from_graphql_input(  # type: ignore[misc] # noqa: E501
            metadata, error_field_name="metadata"
        )

        metadata_manager.store_on_instance(
            metadata_collection, instance, metadata_manager.MetadataType.PUBLIC
        )

        return super().construct_instance(instance, cleaned_data)  # type: ignore[misc] # noqa: E501


class AppImpersonateMixin:
    @classmethod
    def get_user_instance(cls, info, customer_id):
        requester = get_user_or_app_from_context(info.context)
        user = None
        if isinstance(requester, models.User):
            if customer_id:
                raise_validation_error(
                    field="customerId",
                    code=AccountErrorCode.INVALID,
                    message="This field can be used by apps only.",
                )
            user = requester
        elif isinstance(requester, App):
            if not requester.has_perm(AccountPermissions.IMPERSONATE_USER):
                raise PermissionDenied(
                    permissions=[AccountPermissions.IMPERSONATE_USER]
                )
            if not customer_id:
                raise_validation_error(
                    field="customerId",
                    code=AccountErrorCode.REQUIRED,
                    message="This field is required when the mutation is run by app.",
                )
            else:
                user = cls.get_node_or_error(  # type: ignore[attr-defined]
                    info, customer_id, only_type="User", field="customerId"
                )
        return user

import graphene
from django.core.exceptions import ValidationError

from .....account import models
from .....account.error_codes import CustomerTagErrorCode
from .....permission.enums import AccountPermissions
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_324, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import BaseMutation
from ....core.types import BaseInputObjectType, CustomerTagError, NonNullList
from ....core.validators import validate_slug_and_generate_if_needed
from ....meta.inputs import MetadataInput, MetadataInputDescription
from ...types import CustomerTag


class CustomerTagMutationBase(BaseMutation):
    """Shared create/update logic for customer tags.

    Replaces the deprecated `ModelMutation` flow with explicit input cleaning,
    metadata handling, model validation and save.
    """

    customer_tag = graphene.Field(CustomerTag, description="The customer tag.")

    class Meta:
        abstract = True

    @classmethod
    def clean_input(cls, instance, data):
        """Validate/generate the slug and return the cleaned input."""
        cleaned_input = dict(data)
        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "name", cleaned_input
            )
        except ValidationError as error:
            error.code = CustomerTagErrorCode.REQUIRED.value
            raise ValidationError({"slug": error}) from error
        return cleaned_input

    @classmethod
    def save_instance(cls, info: ResolveInfo, instance, cleaned_input):
        """Apply the cleaned input + metadata onto the instance and save it."""
        metadata_list = cleaned_input.pop("metadata", None)
        private_metadata_list = cleaned_input.pop("private_metadata", None)
        metadata_collection = cls.create_metadata_from_graphql_input(
            metadata_list, error_field_name="metadata"
        )
        private_metadata_collection = cls.create_metadata_from_graphql_input(
            private_metadata_list, error_field_name="private_metadata"
        )

        instance = cls.construct_instance(instance, cleaned_input)
        cls.validate_and_update_metadata(
            instance, metadata_collection, private_metadata_collection
        )
        cls.clean_instance(info, instance)
        instance.save()
        return instance


class CustomerTagInput(BaseInputObjectType):
    name = graphene.String(description="Name of the customer tag.")
    slug = graphene.String(description="Slug of the customer tag.")
    description = graphene.String(description="Description of the customer tag.")
    is_public = graphene.Boolean(
        description=(
            "Whether the tag is visible to the storefront owner via `me { tags }`. "
            "Defaults to false."
        ),
    )
    metadata = NonNullList(
        MetadataInput,
        description=(
            "Customer tag public metadata. "
            f"{MetadataInputDescription.PUBLIC_METADATA_INPUT}"
        ),
        required=False,
    )
    private_metadata = NonNullList(
        MetadataInput,
        description=(
            "Customer tag private metadata. "
            f"{MetadataInputDescription.PRIVATE_METADATA_INPUT}"
        ),
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_USERS


class CustomerTagCreateInput(CustomerTagInput):
    name = graphene.String(description="Name of the customer tag.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_USERS


class CustomerTagCreate(CustomerTagMutationBase):
    class Arguments:
        input = CustomerTagCreateInput(
            required=True, description="Fields required to create a customer tag."
        )

    class Meta:
        description = "Create a new customer tag." + ADDED_IN_324 + PREVIEW_FEATURE
        doc_category = DOC_CATEGORY_USERS
        permissions = (AccountPermissions.MANAGE_CUSTOMER_TAGS,)
        error_type_class = CustomerTagError
        support_meta_field = True
        support_private_meta_field = True

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input
    ):
        instance = models.CustomerTag()
        cleaned_input = cls.clean_input(instance, input)
        instance = cls.save_instance(info, instance, cleaned_input)
        return cls(customer_tag=instance)

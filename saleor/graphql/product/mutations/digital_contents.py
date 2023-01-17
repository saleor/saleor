import graphene
from django.core.exceptions import ValidationError

from ....core.exceptions import PermissionDenied
from ....core.permissions import ProductPermissions
from ....product import models
from ....product.error_codes import ProductErrorCode
from ...channel import ChannelContext
from ...core import ResolveInfo
from ...core.context import set_mutation_flag_in_context
from ...core.descriptions import ADDED_IN_38
from ...core.mutations import BaseMutation, ModelMutation
from ...core.types import NonNullList, ProductError, Upload
from ...meta.mutations import MetadataInput
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import DigitalContent, DigitalContentUrl, ProductVariant


class DigitalContentInput(graphene.InputObjectType):
    use_default_settings = graphene.Boolean(
        description="Use default digital content settings for this product.",
        required=True,
    )
    max_downloads = graphene.Int(
        description=(
            "Determines how many times a download link can be accessed by a "
            "customer."
        ),
        required=False,
    )
    url_valid_days = graphene.Int(
        description=(
            "Determines for how many days a download link is active since it "
            "was generated."
        ),
        required=False,
    )
    automatic_fulfillment = graphene.Boolean(
        description="Overwrite default automatic_fulfillment setting for variant.",
        required=False,
    )
    metadata = NonNullList(
        MetadataInput,
        description=(
            "Fields required to update the digital content metadata." + ADDED_IN_38
        ),
        required=False,
    )
    private_metadata = NonNullList(
        MetadataInput,
        description=(
            "Fields required to update the digital content private metadata."
            + ADDED_IN_38
        ),
        required=False,
    )


class DigitalContentUploadInput(DigitalContentInput):
    content_file = Upload(
        required=True, description="Represents an file in a multipart request."
    )


class DigitalContentCreate(BaseMutation):
    variant = graphene.Field(ProductVariant)
    content = graphene.Field(DigitalContent)

    class Arguments:
        variant_id = graphene.ID(
            description="ID of a product variant to upload digital content.",
            required=True,
        )
        input = DigitalContentUploadInput(
            required=True, description="Fields required to create a digital content."
        )

    class Meta:
        description = (
            "Create new digital content. This mutation must be sent as a `multipart` "
            "request. More detailed specs of the upload format can be found here: "
            "https://github.com/jaydenseric/graphql-multipart-request-spec"
        )
        error_type_class = ProductError
        error_type_field = "product_errors"
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        support_meta_field = True
        support_private_meta_field = True

    @classmethod
    def clean_input(cls, info: ResolveInfo, data, instance):
        if hasattr(instance, "digital_content"):
            instance.digital_content.delete()

        use_default_settings = data.get("use_default_settings")
        if use_default_settings:
            return data

        required_fields = ["max_downloads", "url_valid_days", "automatic_fulfillment"]

        if not all(field in data for field in required_fields):
            msg = (
                "Use default settings is disabled. Provide all "
                "missing configuration fields: "
            )
            missing_fields = set(required_fields).difference(set(data))
            if missing_fields:
                msg += "{}, " * len(missing_fields)
                raise ValidationError(
                    msg.format(*missing_fields), code=ProductErrorCode.REQUIRED.value
                )

        return data

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, input, variant_id: str
    ):
        variant = cls.get_node_or_error(
            info, variant_id, field="id", only_type=ProductVariant
        )

        clean_input = cls.clean_input(info, input, variant)

        content_data = info.context.FILES.get(clean_input["content_file"])
        digital_content = models.DigitalContent(content_file=content_data)
        digital_content.use_default_settings = clean_input.get(
            "use_default_settings", False
        )

        digital_content.max_downloads = clean_input.get("max_downloads")
        digital_content.url_valid_days = clean_input.get("url_valid_days")
        digital_content.automatic_fulfillment = clean_input.get(
            "automatic_fulfillment", False
        )
        metadata_list = clean_input.pop("metadata", None)
        private_metadata_list = clean_input.pop("private_metadata", None)

        cls.validate_and_update_metadata(
            digital_content, metadata_list, private_metadata_list
        )

        variant.digital_content = digital_content
        variant.digital_content.save()

        variant = ChannelContext(node=variant, channel_slug=None)
        return DigitalContentCreate(content=digital_content, variant=variant)


class DigitalContentDelete(BaseMutation):
    variant = graphene.Field(ProductVariant)

    class Arguments:
        variant_id = graphene.ID(
            description="ID of a product variant with digital content to remove.",
            required=True,
        )

    class Meta:
        description = "Remove digital content assigned to given variant."
        error_type_class = ProductError
        error_type_field = "product_errors"
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)

    @classmethod
    def mutate(  # type: ignore[override]
        cls, root, info: ResolveInfo, /, *, variant_id: str
    ):
        set_mutation_flag_in_context(info.context)
        if not cls.check_permissions(info.context):
            raise PermissionDenied(permissions=cls._meta.permissions)
        manager = get_plugin_manager_promise(info.context).get()
        result = manager.perform_mutation(
            mutation_cls=cls, root=root, info=info, data={"variant_id": variant_id}
        )
        if result is not None:
            return result

        variant = cls.get_node_or_error(
            info, variant_id, field="id", only_type=ProductVariant
        )

        if hasattr(variant, "digital_content"):
            variant.digital_content.delete()

        variant = ChannelContext(node=variant, channel_slug=None)
        return DigitalContentDelete(variant=variant)


class DigitalContentUpdate(BaseMutation):
    variant = graphene.Field(ProductVariant)
    content = graphene.Field(DigitalContent)

    class Arguments:
        variant_id = graphene.ID(
            description="ID of a product variant with digital content to update.",
            required=True,
        )
        input = DigitalContentInput(
            required=True, description="Fields required to update a digital content."
        )

    class Meta:
        description = "Update digital content."
        error_type_class = ProductError
        error_type_field = "product_errors"
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        support_meta_field = True
        support_private_meta_field = True

    @classmethod
    def clean_input(cls, info: ResolveInfo, data):
        use_default_settings = data.get("use_default_settings")
        if use_default_settings:
            return {"use_default_settings": use_default_settings}

        required_fields = ["max_downloads", "url_valid_days", "automatic_fulfillment"]

        if not all(field in data for field in required_fields):
            msg = (
                "Use default settings is disabled. Provide all "
                "missing configuration fields: "
            )
            missing_fields = set(required_fields).difference(set(data))
            if missing_fields:
                msg += "{}, " * len(missing_fields)
                raise ValidationError(
                    msg.format(*missing_fields), code=ProductErrorCode.REQUIRED.value
                )

        return data

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input, variant_id
    ):
        variant = cls.get_node_or_error(
            info, variant_id, field="id", only_type=ProductVariant
        )

        if not hasattr(variant, "digital_content"):
            msg = f"Variant {variant.id} doesn't have any digital content"
            raise ValidationError(
                {
                    "variantId": ValidationError(
                        msg, code=ProductErrorCode.VARIANT_NO_DIGITAL_CONTENT.value
                    )
                }
            )

        clean_input = cls.clean_input(info, input)

        digital_content = variant.digital_content

        digital_content.use_default_settings = clean_input.get(
            "use_default_settings", False
        )

        digital_content.max_downloads = clean_input.get("max_downloads")
        digital_content.url_valid_days = clean_input.get("url_valid_days")
        digital_content.automatic_fulfillment = clean_input.get(
            "automatic_fulfillment", False
        )

        metadata_list = clean_input.pop("metadata", None)
        private_metadata_list = clean_input.pop("private_metadata", None)

        cls.validate_and_update_metadata(
            digital_content, metadata_list, private_metadata_list
        )

        variant.digital_content = digital_content
        variant.digital_content.save()

        variant = ChannelContext(node=variant, channel_slug=None)
        return DigitalContentUpdate(content=digital_content, variant=variant)


class DigitalContentUrlCreateInput(graphene.InputObjectType):
    content = graphene.ID(
        description="Digital content ID which URL will belong to.",
        name="content",
        required=True,
    )


class DigitalContentUrlCreate(ModelMutation):
    class Arguments:
        input = DigitalContentUrlCreateInput(
            required=True, description="Fields required to create a new url."
        )

    class Meta:
        description = "Generate new URL to digital content."
        model = models.DigitalContentUrl
        object_type = DigitalContentUrl
        error_type_class = ProductError
        error_type_field = "product_errors"
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)

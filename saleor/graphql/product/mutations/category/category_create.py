import graphene
from django.core.exceptions import ValidationError

from .....core.utils.editorjs import clean_editor_js
from .....permission.enums import ProductPermissions
from .....product import models
from .....product.error_codes import ProductErrorCode
from ....core import ResolveInfo
from ....core.descriptions import RICH_CONTENT
from ....core.doc_category import DOC_CATEGORY_PRODUCTS
from ....core.fields import JSONString
from ....core.mutations import DeprecatedModelMutation
from ....core.types import (
    BaseInputObjectType,
    NonNullList,
    ProductError,
    SeoInput,
    Upload,
)
from ....core.validators import clean_seo_fields, validate_slug_and_generate_if_needed
from ....core.validators.file import clean_image_file
from ....meta.inputs import MetadataInput
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Category


class CategoryInput(BaseInputObjectType):
    description = JSONString(description="Category description." + RICH_CONTENT)
    name = graphene.String(description="Category name.")
    slug = graphene.String(description="Category slug.")
    seo = SeoInput(description="Search engine optimization fields.")
    background_image = Upload(description="Background image file.")
    background_image_alt = graphene.String(description="Alt text for a product media.")
    metadata = NonNullList(
        MetadataInput,
        description=("Fields required to update the category metadata."),
        required=False,
    )
    private_metadata = NonNullList(
        MetadataInput,
        description=("Fields required to update the category private metadata."),
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class CategoryCreate(DeprecatedModelMutation):
    class Arguments:
        input = CategoryInput(
            required=True, description="Fields required to create a category."
        )
        parent_id = graphene.ID(
            description=(
                "ID of the parent category. If empty, category will be top level "
                "category."
            ),
            name="parent",
        )

    class Meta:
        description = "Creates a new category."
        model = models.Category
        object_type = Category
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"
        support_meta_field = True
        support_private_meta_field = True

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        description = cleaned_input.get("description")
        cleaned_input["description_plaintext"] = (
            clean_editor_js(description, to_string=True) if description else ""
        )
        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "name", cleaned_input
            )
        except ValidationError as e:
            e.code = ProductErrorCode.REQUIRED.value
            raise ValidationError({"slug": e}) from e
        parent_id = data["parent_id"]
        if parent_id:
            parent = cls.get_node_or_error(
                info, parent_id, field="parent", only_type=Category
            )
            cleaned_input["parent"] = parent
        if data.get("background_image"):
            clean_image_file(cleaned_input, "background_image", ProductErrorCode)
        clean_seo_fields(cleaned_input)
        return cleaned_input

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        parent_id = data.pop("parent_id", None)
        data["input"]["parent_id"] = parent_id
        return super().perform_mutation(root, info, **data)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, _cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.category_created, instance)

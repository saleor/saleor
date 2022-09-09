from typing import TYPE_CHECKING

import graphene
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Exists, OuterRef, Q
from django.utils.text import slugify

from ...attribute import ATTRIBUTE_PROPERTIES_CONFIGURATION, AttributeInputType
from ...attribute import models as models
from ...attribute.error_codes import AttributeErrorCode
from ...core.exceptions import PermissionDenied
from ...core.permissions import (
    PageTypePermissions,
    ProductPermissions,
    ProductTypePermissions,
)
from ...core.tracing import traced_atomic_transaction
from ...core.utils import generate_unique_slug
from ...product import models as product_models
from ..core.enums import MeasurementUnitsEnum
from ..core.fields import JSONString
from ..core.inputs import ReorderInput
from ..core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ..core.types import AttributeError, NonNullList
from ..core.utils import validate_slug_and_generate_if_needed
from ..core.utils.reordering import perform_reordering
from .descriptions import AttributeDescriptions, AttributeValueDescriptions
from .enums import AttributeEntityTypeEnum, AttributeInputTypeEnum, AttributeTypeEnum
from .types import Attribute, AttributeValue

if TYPE_CHECKING:
    from django.db.models import QuerySet


class BaseReorderAttributesMutation(BaseMutation):
    class Meta:
        abstract = True

    @classmethod
    def prepare_operations(cls, moves: ReorderInput, attributes: "QuerySet"):
        """Prepare operations dict for reordering attributes.

        Operation dict format:
            key: attribute pk,
            value: sort_order value - relative sorting position of the attribute
        """
        attribute_ids = []
        sort_orders = []

        # resolve attribute moves
        for move_info in moves:
            attribute_ids.append(move_info.id)
            sort_orders.append(move_info.sort_order)

        attr_pks = cls.get_global_ids_or_error(attribute_ids, Attribute)
        attr_pks = [int(pk) for pk in attr_pks]

        attributes_m2m = attributes.filter(attribute_id__in=attr_pks)

        if attributes_m2m.count() != len(attr_pks):
            attribute_pks = attributes_m2m.values_list("attribute_id", flat=True)
            invalid_attrs = set(attr_pks) - set(attribute_pks)
            invalid_attr_ids = [
                graphene.Node.to_global_id("Attribute", attr_pk)
                for attr_pk in invalid_attrs
            ]
            raise ValidationError(
                "Couldn't resolve to an attribute.",
                params={"attributes": invalid_attr_ids},
            )

        attributes_m2m = list(attributes_m2m)
        attributes_m2m.sort(
            key=lambda e: attr_pks.index(e.attribute.pk)
        )  # preserve order in pks

        operations = {
            attribute.pk: sort_order
            for attribute, sort_order in zip(attributes_m2m, sort_orders)
        }

        return operations


class BaseReorderAttributeValuesMutation(BaseMutation):
    class Meta:
        abstract = True

    @classmethod
    def perform(
        cls,
        instance_id: str,
        instance_type: str,
        data: dict,
        assignment_lookup: str,
        error_code_enum,
    ):
        attribute_id = data["attribute_id"]
        moves = data["moves"]

        instance = cls.get_instance(instance_id)
        attribute_assignment = cls.get_attribute_assignment(
            instance, instance_type, attribute_id, error_code_enum
        )
        values_m2m = getattr(attribute_assignment, assignment_lookup)

        try:
            operations = cls.prepare_operations(moves, values_m2m)
        except ValidationError as error:
            error.code = error_code_enum.NOT_FOUND.value
            raise ValidationError({"moves": error})

        with traced_atomic_transaction():
            perform_reordering(values_m2m, operations)

        return instance

    @staticmethod
    def get_instance(instance_id: str):
        pass

    @classmethod
    def get_attribute_assignment(
        cls, instance, instance_type, attribute_id: str, error_code_enum
    ):
        attribute_pk = cls.get_global_id_or_error(
            attribute_id, only_type=Attribute, field="attribute_id"
        )

        try:
            attribute_assignment = instance.attributes.prefetch_related("values").get(
                assignment__attribute_id=attribute_pk  # type: ignore
            )
        except ObjectDoesNotExist:
            raise ValidationError(
                {
                    "attribute_id": ValidationError(
                        f"Couldn't resolve to a {instance_type} "
                        f"attribute: {attribute_id}.",
                        code=error_code_enum.NOT_FOUND.value,
                    )
                }
            )
        return attribute_assignment

    @classmethod
    def prepare_operations(cls, moves: ReorderInput, values: "QuerySet"):
        """Prepare operations dict for reordering attribute values.

        Operation dict format:
            key: attribute value pk,
            value: sort_order value - relative sorting position of the attribute
        """
        value_ids = []
        sort_orders = []

        # resolve attribute moves
        for move_info in moves:
            value_ids.append(move_info.id)
            sort_orders.append(move_info.sort_order)

        values_pks = cls.get_global_ids_or_error(value_ids, AttributeValue)
        values_pks = [int(pk) for pk in values_pks]

        values_m2m = values.filter(value_id__in=values_pks)

        if values_m2m.count() != len(values_pks):
            pks = values_m2m.values_list("value_id", flat=True)
            invalid_values = set(values_pks) - set(pks)
            invalid_ids = [
                graphene.Node.to_global_id("AttributeValue", val_pk)
                for val_pk in invalid_values
            ]
            raise ValidationError(
                "Couldn't resolve to an attribute value.",
                params={"values": invalid_ids},
            )

        values_m2m = list(values_m2m)
        values_m2m.sort(
            key=lambda e: values_pks.index(e.value_id)
        )  # preserve order in pks

        operations = {
            value.pk: sort_order for value, sort_order in zip(values_m2m, sort_orders)
        }

        return operations


class AttributeValueInput(graphene.InputObjectType):
    value = graphene.String(description=AttributeValueDescriptions.VALUE)
    rich_text = JSONString(description=AttributeValueDescriptions.RICH_TEXT)
    plain_text = graphene.String(description=AttributeValueDescriptions.PLAIN_TEXT)
    file_url = graphene.String(
        required=False,
        description="URL of the file attribute. Every time, a new value is created.",
    )
    content_type = graphene.String(required=False, description="File content type.")


class AttributeValueCreateInput(AttributeValueInput):
    name = graphene.String(required=True, description=AttributeValueDescriptions.NAME)


class AttributeValueUpdateInput(AttributeValueInput):
    name = graphene.String(required=False, description=AttributeValueDescriptions.NAME)


class AttributeCreateInput(graphene.InputObjectType):
    input_type = AttributeInputTypeEnum(description=AttributeDescriptions.INPUT_TYPE)
    entity_type = AttributeEntityTypeEnum(description=AttributeDescriptions.ENTITY_TYPE)
    name = graphene.String(required=True, description=AttributeDescriptions.NAME)
    slug = graphene.String(required=False, description=AttributeDescriptions.SLUG)
    type = AttributeTypeEnum(description=AttributeDescriptions.TYPE, required=True)
    unit = MeasurementUnitsEnum(description=AttributeDescriptions.UNIT, required=False)
    values = NonNullList(
        AttributeValueCreateInput, description=AttributeDescriptions.VALUES
    )
    value_required = graphene.Boolean(description=AttributeDescriptions.VALUE_REQUIRED)
    is_variant_only = graphene.Boolean(
        required=False, description=AttributeDescriptions.IS_VARIANT_ONLY
    )
    visible_in_storefront = graphene.Boolean(
        description=AttributeDescriptions.VISIBLE_IN_STOREFRONT
    )
    filterable_in_storefront = graphene.Boolean(
        description=AttributeDescriptions.FILTERABLE_IN_STOREFRONT
    )
    filterable_in_dashboard = graphene.Boolean(
        description=AttributeDescriptions.FILTERABLE_IN_DASHBOARD
    )
    storefront_search_position = graphene.Int(
        required=False, description=AttributeDescriptions.STOREFRONT_SEARCH_POSITION
    )
    available_in_grid = graphene.Boolean(
        required=False, description=AttributeDescriptions.AVAILABLE_IN_GRID
    )


class AttributeUpdateInput(graphene.InputObjectType):
    name = graphene.String(description=AttributeDescriptions.NAME)
    slug = graphene.String(description=AttributeDescriptions.SLUG)
    unit = MeasurementUnitsEnum(description=AttributeDescriptions.UNIT, required=False)
    remove_values = NonNullList(
        graphene.ID,
        name="removeValues",
        description="IDs of values to be removed from this attribute.",
    )
    add_values = NonNullList(
        AttributeValueUpdateInput,
        name="addValues",
        description="New values to be created for this attribute.",
    )
    value_required = graphene.Boolean(description=AttributeDescriptions.VALUE_REQUIRED)
    is_variant_only = graphene.Boolean(
        required=False, description=AttributeDescriptions.IS_VARIANT_ONLY
    )
    visible_in_storefront = graphene.Boolean(
        description=AttributeDescriptions.VISIBLE_IN_STOREFRONT
    )
    filterable_in_storefront = graphene.Boolean(
        description=AttributeDescriptions.FILTERABLE_IN_STOREFRONT
    )
    filterable_in_dashboard = graphene.Boolean(
        description=AttributeDescriptions.FILTERABLE_IN_DASHBOARD
    )
    storefront_search_position = graphene.Int(
        required=False, description=AttributeDescriptions.STOREFRONT_SEARCH_POSITION
    )
    available_in_grid = graphene.Boolean(
        required=False, description=AttributeDescriptions.AVAILABLE_IN_GRID
    )


class AttributeMixin:
    # must be redefined by inheriting classes
    ATTRIBUTE_VALUES_FIELD: str

    @classmethod
    def clean_values(cls, cleaned_input, attribute):
        """Clean attribute values.

        Transforms AttributeValueCreateInput into AttributeValue instances.
        Slugs are created from given names and checked for uniqueness within
        an attribute.
        """
        values_input = cleaned_input.get(cls.ATTRIBUTE_VALUES_FIELD)
        attribute_input_type = cleaned_input.get("input_type") or attribute.input_type

        if values_input is None:
            return

        if (
            attribute_input_type
            in [AttributeInputType.FILE, AttributeInputType.REFERENCE]
            and values_input
        ):
            raise ValidationError(
                {
                    cls.ATTRIBUTE_VALUES_FIELD: ValidationError(
                        "Values cannot be used with "
                        f"input type {attribute_input_type}.",
                        code=AttributeErrorCode.INVALID.value,
                    )
                }
            )

        is_numeric_attr = attribute_input_type == AttributeInputType.NUMERIC
        is_swatch_attr = attribute_input_type == AttributeInputType.SWATCH
        for value_data in values_input:
            cls.validate_value(attribute, value_data, is_numeric_attr, is_swatch_attr)

        cls.check_values_are_unique(values_input, attribute)

    @classmethod
    def validate_value(
        cls,
        attribute: models.Attribute,
        value_data: dict,
        is_numeric_attr: bool,
        is_swatch_attr: bool,
    ):
        value = value_data["name"]
        cls.clean_value_input_data(value_data, is_swatch_attr)

        if is_numeric_attr:
            cls.validate_numeric_value(value)
        elif is_swatch_attr:
            cls.validate_swatch_attr_value(value_data)

        slug_value = value if not is_numeric_attr else value.replace(".", "_")
        value_data["slug"] = slugify(slug_value, allow_unicode=True)

        attribute_value = models.AttributeValue(**value_data, attribute=attribute)
        try:
            attribute_value.full_clean()
        except ValidationError as validation_errors:
            for field, err in validation_errors.error_dict.items():
                if field == "attribute":
                    continue
                raise ValidationError({cls.ATTRIBUTE_VALUES_FIELD: err})

    @classmethod
    def clean_value_input_data(cls, value_data: dict, is_swatch_attr: bool):
        swatch_fields = ["file_url", "content_type", "value"]
        if not is_swatch_attr and any(
            [value_data.get(field) for field in swatch_fields]
        ):
            raise ValidationError(
                {
                    cls.ATTRIBUTE_VALUES_FIELD: ValidationError(
                        "Cannot define value, file and contentType fields "
                        "for not swatch attribute.",
                        code=AttributeErrorCode.INVALID.value,
                    )
                }
            )

    @classmethod
    def validate_numeric_value(cls, value):
        try:
            float(value)
        except ValueError:
            raise ValidationError(
                {
                    cls.ATTRIBUTE_VALUES_FIELD: ValidationError(
                        "Value of numeric attribute must be numeric.",
                        code=AttributeErrorCode.INVALID.value,
                    )
                }
            )

    @classmethod
    def validate_swatch_attr_value(cls, value_data: dict):
        if value_data.get("value") and value_data.get("file_url"):
            raise ValidationError(
                {
                    cls.ATTRIBUTE_VALUES_FIELD: ValidationError(
                        "Cannot specify both value and file for swatch attribute.",
                        code=AttributeErrorCode.INVALID.value,
                    )
                }
            )

    @classmethod
    def check_values_are_unique(cls, values_input: dict, attribute: models.Attribute):
        # Check values uniqueness in case of creating new attribute.
        existing_values = attribute.values.values_list("slug", flat=True)
        for value_data in values_input:
            slug = slugify(value_data["name"], allow_unicode=True)
            if slug in existing_values:
                msg = (
                    "Value %s already exists within this attribute."
                    % value_data["name"]
                )
                raise ValidationError(
                    {
                        cls.ATTRIBUTE_VALUES_FIELD: ValidationError(
                            msg, code=AttributeErrorCode.ALREADY_EXISTS.value
                        )
                    }
                )

        new_slugs = [
            slugify(value_data["name"], allow_unicode=True)
            for value_data in values_input
        ]
        if len(set(new_slugs)) != len(new_slugs):
            raise ValidationError(
                {
                    cls.ATTRIBUTE_VALUES_FIELD: ValidationError(
                        "Provided values are not unique.",
                        code=AttributeErrorCode.UNIQUE.value,
                    )
                }
            )

    @classmethod
    def clean_attribute(cls, instance, cleaned_input):
        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "name", cleaned_input
            )
        except ValidationError as error:
            error.code = AttributeErrorCode.REQUIRED.value
            raise ValidationError({"slug": error})
        cls._clean_attribute_settings(instance, cleaned_input)

        return cleaned_input

    @classmethod
    def _clean_attribute_settings(cls, instance, cleaned_input):
        """Validate attributes settings.

        Ensure that any invalid operations will be not performed.
        """
        attribute_input_type = cleaned_input.get("input_type") or instance.input_type
        errors = {}
        for field in ATTRIBUTE_PROPERTIES_CONFIGURATION.keys():
            allowed_input_type = ATTRIBUTE_PROPERTIES_CONFIGURATION[field]
            if attribute_input_type not in allowed_input_type and cleaned_input.get(
                field
            ):
                errors[field] = ValidationError(
                    f"Cannot set {field} on a {attribute_input_type} attribute.",
                    code=AttributeErrorCode.INVALID.value,
                )
        if errors:
            raise ValidationError(errors)

    @classmethod
    def _save_m2m(cls, info, attribute, cleaned_data):
        super()._save_m2m(info, attribute, cleaned_data)
        values = cleaned_data.get(cls.ATTRIBUTE_VALUES_FIELD) or []
        for value in values:
            attribute.values.create(**value)


class AttributeCreate(AttributeMixin, ModelMutation):
    # Needed by AttributeMixin,
    # represents the input name for the passed list of values
    ATTRIBUTE_VALUES_FIELD = "values"

    attribute = graphene.Field(Attribute, description="The created attribute.")

    class Arguments:
        input = AttributeCreateInput(
            required=True, description="Fields required to create an attribute."
        )

    class Meta:
        model = models.Attribute
        object_type = Attribute
        description = "Creates an attribute."
        error_type_class = AttributeError
        error_type_field = "attribute_errors"

    @classmethod
    def clean_input(cls, info, instance, data, input_cls=None):
        cleaned_input = super().clean_input(info, instance, data, input_cls)
        if cleaned_input.get(
            "input_type"
        ) == AttributeInputType.REFERENCE and not cleaned_input.get("entity_type"):
            raise ValidationError(
                {
                    "entity_type": ValidationError(
                        "Entity type is required when REFERENCE input type is used.",
                        code=AttributeErrorCode.REQUIRED.value,
                    )
                }
            )
        return cleaned_input

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        input = data.get("input")
        # check permissions based on attribute type
        if input["type"] == AttributeTypeEnum.PRODUCT_TYPE.value:
            permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        else:
            permissions = (PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,)
        if not cls.check_permissions(info.context, permissions):
            raise PermissionDenied(permissions=permissions)

        instance = models.Attribute()

        # Do cleaning and uniqueness checks
        cleaned_input = cls.clean_input(info, instance, input)
        cls.clean_attribute(instance, cleaned_input)
        cls.clean_values(cleaned_input, instance)

        # Construct the attribute
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(info, instance)

        # Commit it
        instance.save()
        cls._save_m2m(info, instance, cleaned_input)
        cls.post_save_action(info, instance, cleaned_input)
        # Return the attribute that was created
        return AttributeCreate(attribute=instance)

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        info.context.plugins.attribute_created(instance)


class AttributeUpdate(AttributeMixin, ModelMutation):
    # Needed by AttributeMixin,
    # represents the input name for the passed list of values
    ATTRIBUTE_VALUES_FIELD = "add_values"

    attribute = graphene.Field(Attribute, description="The updated attribute.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of an attribute to update.")
        input = AttributeUpdateInput(
            required=True, description="Fields required to update an attribute."
        )

    class Meta:
        model = models.Attribute
        object_type = Attribute
        description = "Updates attribute."
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        error_type_class = AttributeError
        error_type_field = "attribute_errors"

    @classmethod
    def clean_remove_values(cls, cleaned_input, instance):
        """Check if the values to be removed are assigned to the given attribute."""
        remove_values = cleaned_input.get("remove_values", [])
        for value in remove_values:
            if value.attribute != instance:
                msg = "Value %s does not belong to this attribute." % value
                raise ValidationError(
                    {
                        "remove_values": ValidationError(
                            msg, code=AttributeErrorCode.INVALID
                        )
                    }
                )
        return remove_values

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        for attribute_value in cleaned_data.get("remove_values", []):
            attribute_value.delete()

    @classmethod
    def perform_mutation(cls, _root, info, id, input):
        instance = cls.get_node_or_error(info, id, only_type=Attribute)

        # Do cleaning and uniqueness checks
        cleaned_input = cls.clean_input(info, instance, input)
        cls.clean_attribute(instance, cleaned_input)
        cls.clean_values(cleaned_input, instance)
        cls.clean_remove_values(cleaned_input, instance)

        # Construct the attribute
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(info, instance)

        # Commit it
        instance.save()
        cls._save_m2m(info, instance, cleaned_input)
        cls.post_save_action(info, instance, cleaned_input)

        # Return the attribute that was created
        return AttributeUpdate(attribute=instance)

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        info.context.plugins.attribute_updated(instance)


class AttributeDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of an attribute to delete.")

    class Meta:
        model = models.Attribute
        object_type = Attribute
        description = "Deletes an attribute."
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        error_type_class = AttributeError
        error_type_field = "attribute_errors"

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        info.context.plugins.attribute_deleted(instance)


def validate_value_is_unique(attribute: models.Attribute, value: models.AttributeValue):
    """Check if the attribute value is unique within the attribute it belongs to."""
    duplicated_values = attribute.values.exclude(pk=value.pk).filter(slug=value.slug)
    if duplicated_values.exists():
        raise ValidationError(
            {
                "name": ValidationError(
                    f"Value with slug {value.slug} already exists.",
                    code=AttributeErrorCode.ALREADY_EXISTS.value,
                )
            }
        )


class AttributeValueCreate(AttributeMixin, ModelMutation):
    ATTRIBUTE_VALUES_FIELD = "input"

    attribute = graphene.Field(Attribute, description="The updated attribute.")

    class Arguments:
        attribute_id = graphene.ID(
            required=True,
            name="attribute",
            description="Attribute to which value will be assigned.",
        )
        input = AttributeValueCreateInput(
            required=True, description="Fields required to create an AttributeValue."
        )

    class Meta:
        model = models.AttributeValue
        object_type = AttributeValue
        description = "Creates a value for an attribute."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = AttributeError
        error_type_field = "attribute_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        if "name" in cleaned_input:
            cleaned_input["slug"] = generate_unique_slug(
                instance,
                cleaned_input["name"],
                additional_search_lookup={"attribute_id": instance.attribute_id},
            )
        input_type = instance.attribute.input_type

        is_swatch_attr = input_type == AttributeInputType.SWATCH
        only_swatch_fields = ["file_url", "content_type"]
        errors = {}
        if not is_swatch_attr:
            for field in only_swatch_fields:
                if cleaned_input.get(field):
                    errors[field] = ValidationError(
                        f"The field {field} can be defined only for swatch attributes.",
                        code=AttributeErrorCode.INVALID.value,
                    )
        else:
            try:
                cls.validate_swatch_attr_value(cleaned_input)
            except ValidationError as error:
                errors["value"] = error.error_dict[cls.ATTRIBUTE_VALUES_FIELD]
                errors["fileUrl"] = error.error_dict[cls.ATTRIBUTE_VALUES_FIELD]
        if errors:
            raise ValidationError(errors)

        return cleaned_input

    @classmethod
    def clean_instance(cls, info, instance):
        validate_value_is_unique(instance.attribute, instance)
        super().clean_instance(info, instance)

    @classmethod
    def perform_mutation(cls, _root, info, attribute_id, input):
        attribute = cls.get_node_or_error(info, attribute_id, only_type=Attribute)
        instance = models.AttributeValue(attribute=attribute)
        cleaned_input = cls.clean_input(info, instance, input)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(info, instance)

        instance.save()
        cls._save_m2m(info, instance, cleaned_input)
        cls.post_save_action(info, instance, cleaned_input)
        return AttributeValueCreate(attribute=attribute, attributeValue=instance)

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        info.context.plugins.attribute_value_created(instance)
        info.context.plugins.attribute_updated(instance.attribute)


class AttributeValueUpdate(AttributeValueCreate):
    attribute = graphene.Field(Attribute, description="The updated attribute.")

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of an AttributeValue to update."
        )
        input = AttributeValueUpdateInput(
            required=True, description="Fields required to update an AttributeValue."
        )

    class Meta:
        model = models.AttributeValue
        object_type = AttributeValue
        description = "Updates value of an attribute."
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        error_type_class = AttributeError
        error_type_field = "attribute_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        if cleaned_input.get("value"):
            cleaned_input["file_url"] = ""
            cleaned_input["content_type"] = ""
        elif cleaned_input.get("file_url"):
            cleaned_input["value"] = ""
        return cleaned_input

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        return super(AttributeValueCreate, cls).perform_mutation(_root, info, **data)

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.attribute = instance.attribute
        return response

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        variants = product_models.ProductVariant.objects.filter(
            Exists(instance.variantassignments.filter(variant_id=OuterRef("id")))
        )

        product_models.Product.objects.filter(
            Q(Exists(instance.productassignments.filter(product_id=OuterRef("id"))))
            | Q(Exists(variants.filter(product_id=OuterRef("id"))))
        ).update(search_index_dirty=True)

        info.context.plugins.attribute_value_updated(instance)
        info.context.plugins.attribute_updated(instance.attribute)


class AttributeValueDelete(ModelDeleteMutation):
    attribute = graphene.Field(Attribute, description="The updated attribute.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of a value to delete.")

    class Meta:
        model = models.AttributeValue
        object_type = AttributeValue
        description = "Deletes a value of an attribute."
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        error_type_class = AttributeError
        error_type_field = "attribute_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        node_id = data.get("id")
        instance = cls.get_node_or_error(info, node_id, only_type=AttributeValue)
        product_ids = cls.get_product_ids_to_update(instance)
        response = super().perform_mutation(_root, info, **data)
        product_models.Product.objects.filter(id__in=product_ids).update(
            search_index_dirty=True
        )
        info.context.plugins.attribute_value_deleted(instance)
        info.context.plugins.attribute_updated(instance.attribute)
        return response

    @classmethod
    def get_product_ids_to_update(cls, instance):
        variants = product_models.ProductVariant.objects.filter(
            Exists(instance.variantassignments.filter(variant_id=OuterRef("id")))
        )
        product_ids = product_models.Product.objects.filter(
            Q(Exists(instance.productassignments.filter(product_id=OuterRef("id"))))
            | Q(Exists(variants.filter(product_id=OuterRef("id"))))
        ).values_list("id", flat=True)
        return list(product_ids)

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.attribute = instance.attribute
        return response


class AttributeReorderValues(BaseMutation):
    attribute = graphene.Field(
        Attribute, description="Attribute from which values are reordered."
    )

    class Meta:
        description = "Reorder the values of an attribute."
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        error_type_class = AttributeError
        error_type_field = "attribute_errors"

    class Arguments:
        attribute_id = graphene.Argument(
            graphene.ID, required=True, description="ID of an attribute."
        )
        moves = NonNullList(
            ReorderInput,
            required=True,
            description="The list of reordering operations for given attribute values.",
        )

    @classmethod
    def perform_mutation(cls, _root, info, attribute_id, moves):
        pk = cls.get_global_id_or_error(
            attribute_id, only_type=Attribute, field="attribute_id"
        )

        try:
            attribute = models.Attribute.objects.prefetch_related("values").get(pk=pk)
        except ObjectDoesNotExist:
            raise ValidationError(
                {
                    "attribute_id": ValidationError(
                        f"Couldn't resolve to an attribute: {attribute_id}",
                        code=AttributeErrorCode.NOT_FOUND,
                    )
                }
            )

        values_m2m = attribute.values.all()
        operations = {}

        # Resolve the values
        for move_info in moves:
            value_pk = cls.get_global_id_or_error(
                move_info.id, only_type=AttributeValue, field="moves"
            )

            try:
                m2m_info = values_m2m.get(pk=int(value_pk))
            except ObjectDoesNotExist:
                raise ValidationError(
                    {
                        "moves": ValidationError(
                            f"Couldn't resolve to an attribute value: {move_info.id}",
                            code=AttributeErrorCode.NOT_FOUND,
                        )
                    }
                )
            operations[m2m_info.pk] = move_info.sort_order

        with traced_atomic_transaction():
            perform_reordering(values_m2m, operations)
        attribute.refresh_from_db(fields=["values"])

        for value in [v for v in values_m2m if v.id in operations.keys()]:
            info.context.plugins.attribute_value_updated(value)
        info.context.plugins.attribute_updated(attribute)

        return AttributeReorderValues(attribute=attribute)

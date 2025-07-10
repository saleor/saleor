import abc
import datetime
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple, cast

import graphene
from django.core.exceptions import ValidationError
from django.db.models import Model, Q
from django.db.models.expressions import Exists, OuterRef
from django.template.defaultfilters import truncatechars
from django.utils.text import slugify
from graphql.error import GraphQLError
from text_unidecode import unidecode

from ...attribute import AttributeEntityType, AttributeInputType
from ...attribute import models as attribute_models
from ...attribute.models import AttributeValue
from ...attribute.utils import associate_attribute_values_to_instance
from ...core.utils import (
    generate_unique_slug,
    prepare_unique_attribute_value_slug,
    prepare_unique_slug,
)
from ...core.utils.editorjs import clean_editor_js
from ...core.utils.url import get_default_storage_root_url
from ...page import models as page_models
from ...page.error_codes import PageErrorCode
from ...product import models as product_models
from ...product.error_codes import ProductErrorCode
from ..core.utils import from_global_id_or_error, get_duplicated_values
from ..core.validators import validate_one_of_args_is_in_mutation
from ..product.utils import get_used_attribute_values_for_variant
from ..utils import get_nodes
from .enums import AttributeValueBulkActionEnum

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from ...attribute.models import Attribute


@dataclass
class AttrValuesForSelectableFieldInput:
    id: str | None = None
    external_reference: str | None = None
    value: str | None = None


@dataclass
class AttrValuesInput:
    global_id: str | None
    external_reference: str | None = None
    values: list[str] | None = None
    dropdown: AttrValuesForSelectableFieldInput | None = None
    swatch: AttrValuesForSelectableFieldInput | None = None
    multiselect: list[AttrValuesForSelectableFieldInput] | None = None
    numeric: str | None = None
    references: list[str] | list[page_models.Page] | None = None
    file_url: str | None = None
    content_type: str | None = None
    rich_text: dict | None = None
    plain_text: str | None = None
    boolean: bool | None = None
    date: datetime.date | None = None
    date_time: datetime.datetime | None = None


T_INSTANCE = product_models.Product | product_models.ProductVariant | page_models.Page
T_INPUT_MAP = list[tuple[attribute_models.Attribute, AttrValuesInput]]
T_ERROR_DICT = dict[tuple[str, str], list]


class EntityTypeData(NamedTuple):
    """Defines metadata for a referenceable entity type."""

    model: type[Model]
    name_field: str
    value_field: str


ENTITY_TYPE_MAPPING = {
    AttributeEntityType.PAGE: EntityTypeData(
        page_models.Page, "title", "reference_page"
    ),
    AttributeEntityType.PRODUCT: EntityTypeData(
        product_models.Product, "name", "reference_product"
    ),
    AttributeEntityType.PRODUCT_VARIANT: EntityTypeData(
        product_models.ProductVariant, "name", "reference_variant"
    ),
    AttributeEntityType.CATEGORY: EntityTypeData(
        product_models.Category, "name", "reference_category"
    ),
    AttributeEntityType.COLLECTION: EntityTypeData(
        product_models.Collection, "name", "reference_collection"
    ),
}


class AttributeInputErrors:
    """Defines error messages and codes for attribute validation."""

    # General Errors
    ID_OR_EXTERNAL_REFERENCE_REQUIRED = (
        "Attribute 'id' or 'externalReference' must be provided.",
        "REQUIRED",
    )
    VALUE_REQUIRED = ("This attribute requires a value.", "REQUIRED")
    BLANK_VALUE = ("Attribute values cannot be blank.", "REQUIRED")
    DUPLICATED_VALUES = (
        "Duplicate attribute values are not allowed.",
        "DUPLICATED_INPUT_ITEM",
    )
    INVALID_INPUT = ("Invalid value provided for attribute.", "INVALID")
    MORE_THAN_ONE_VALUE = ("Attribute must take only one value.", "INVALID")

    # Selectable Field Errors
    ID_AND_VALUE_PROVIDED = (
        "Provide either 'id' or 'value' for a selectable attribute, not both.",
        "INVALID",
    )
    ID_AND_EXTERNAL_REFERENCE_PROVIDED = (
        "Provide either 'id' or 'externalReference', not both.",
        "INVALID",
    )
    MAX_LENGTH_EXCEEDED = ("The value exceeds the maximum length.", "INVALID")

    # File Errors
    FILE_URL_REQUIRED = ("A file URL is required for this attribute.", "REQUIRED")
    INVALID_FILE_URL = (
        "The file_url must be the path to the default storage.",
        "INVALID",
    )

    # Reference Errors
    REFERENCE_REQUIRED = ("A reference is required for this attribute.", "REQUIRED")
    INVALID_REFERENCE = ("Invalid reference type.", "INVALID")


class AttributeTypeHandler(abc.ABC):
    """Abstract base class for attribute type-specific logic."""

    def __init__(
        self,
        attribute: "Attribute",
        values_input: AttrValuesInput,
        error_code_enum: type[ProductErrorCode | PageErrorCode],
    ):
        self.attribute = attribute
        self.values_input = values_input
        self.attribute_identifier = (
            values_input.global_id or values_input.external_reference
        )
        self.error_code_enum = error_code_enum
        self.attr_identifier = values_input.global_id or values_input.external_reference

    @abc.abstractmethod
    def clean_and_validate(self, attribute_errors: T_ERROR_DICT):
        """Clean, resolve, and validate input values."""

        raise NotImplementedError

    @abc.abstractmethod
    def pre_save_value(
        self, instance: T_INSTANCE
    ) -> list[tuple[AttributeValueBulkActionEnum, dict | AttributeValue]]:
        """Prepare attribute value data for bulk database operations."""

        raise NotImplementedError

    def _validate_selectable_field(
        self,
        attr_value_input: AttrValuesForSelectableFieldInput,
        value_required: bool,
        attribute_errors: T_ERROR_DICT,
    ):
        """Validate a single input for a selectable field."""

        id, value, ext_ref = (
            attr_value_input.id,
            attr_value_input.value,
            attr_value_input.external_reference,
        )

        # Check for conflicting identifiers
        if id and ext_ref:
            attribute_errors[
                AttributeInputErrors.ID_AND_EXTERNAL_REFERENCE_PROVIDED
            ].append(self.attribute_identifier)
        if id and value:
            attribute_errors[AttributeInputErrors.ID_AND_VALUE_PROVIDED].append(
                self.attribute_identifier
            )

        # Check for an empty input object `{}`, which is invalid.
        if value_required and (not id and not value and not ext_ref):
            attribute_errors[AttributeInputErrors.VALUE_REQUIRED].append(
                self.attribute_identifier
            )

        # Validate the `value` field if provided
        if value:
            max_length = self.attribute.values.model.name.field.max_length
            if not value.strip():
                attribute_errors[AttributeInputErrors.BLANK_VALUE].append(
                    self.attribute_identifier
                )
            elif max_length and len(value) > max_length:
                attribute_errors[AttributeInputErrors.MAX_LENGTH_EXCEEDED].append(
                    self.attribute_identifier
                )

    def _update_or_create_value(
        self,
        instance: T_INSTANCE,
        value_defaults: dict,
    ):
        slug = slugify(unidecode(f"{instance.id}_{self.attribute.id}"))
        value = {
            "attribute": self.attribute,
            "slug": slug,
            "defaults": value_defaults,
        }
        return [
            (AttributeValueBulkActionEnum.UPDATE_OR_CREATE, value),
        ]


class SelectableAttributeHandler(AttributeTypeHandler):
    """Handler for Dropdown and Swatch attribute types."""

    def get_selectable_input(self) -> AttrValuesForSelectableFieldInput | None:
        """Get the specific input object for dropdown or swatch."""

        if self.attribute.input_type == AttributeInputType.DROPDOWN:
            return self.values_input.dropdown
        if self.attribute.input_type == AttributeInputType.SWATCH:
            return self.values_input.swatch
        return None

    def clean_and_validate(self, attribute_errors: T_ERROR_DICT):
        selectable_input = self.get_selectable_input()

        if not selectable_input:
            if self.attribute.value_required:
                attribute_errors[AttributeInputErrors.VALUE_REQUIRED].append(
                    self.attribute_identifier
                )
            return

        # Use the helper method from the base class
        self._validate_selectable_field(
            selectable_input,
            value_required=self.attribute.value_required,
            attribute_errors=attribute_errors,
        )

    def pre_save_value(self, instance: T_INSTANCE) -> list[tuple]:
        selectable_input = self.get_selectable_input()
        if not selectable_input:
            return []

        id, value, ext_ref = (
            selectable_input.id,
            selectable_input.value,
            selectable_input.external_reference,
        )

        if ext_ref and value:
            slug = prepare_unique_attribute_value_slug(
                self.attribute, slugify(unidecode(value))
            )
            value_obj = AttributeValue(
                attribute=self.attribute,
                name=value,
                slug=slug,
                external_reference=ext_ref,
            )
            return [(AttributeValueBulkActionEnum.CREATE, value_obj)]

        if ext_ref or id:
            try:
                if ext_ref:
                    value_obj = self.attribute.values.get(external_reference=ext_ref)
                else:
                    _, pk = from_global_id_or_error(id, "AttributeValue")  # type: ignore[arg-type]
                    value_obj = self.attribute.values.get(pk=pk)
                return [(AttributeValueBulkActionEnum.NONE, value_obj)]
            except (GraphQLError, AttributeValue.DoesNotExist) as e:
                raise ValidationError(
                    f"AttributeValue not found: {e}",
                    code=ProductErrorCode.NOT_FOUND.value,
                ) from e

        if value:
            return AttributeAssignmentMixin._prepare_attribute_values(
                self.attribute, [value]
            )

        return []


class MultiSelectableAttributeHandler(AttributeTypeHandler):
    """Handler for Multiselect attribute type."""

    def clean_and_validate(self, attribute_errors: T_ERROR_DICT):
        multi_values = self.values_input.multiselect

        if not multi_values:
            if self.attribute.value_required:
                attribute_errors[AttributeInputErrors.VALUE_REQUIRED].append(
                    self.attribute_identifier
                )
            return

        ids = [value.id for value in multi_values if value.id is not None]
        values = [value.value for value in multi_values if value.value is not None]
        external_refs = [
            value.external_reference
            for value in multi_values
            if value.external_reference is not None
        ]
        if ids and values:
            attribute_errors[AttributeInputErrors.ID_AND_VALUE_PROVIDED].append(
                self.attribute_identifier
            )
        elif (
            not ids
            and not external_refs
            and not values
            and self.attribute.value_required
        ):
            attribute_errors[AttributeInputErrors.VALUE_REQUIRED].append(
                self.attribute_identifier
            )
        elif (
            len(ids) > len(set(ids))
            or len(values) > len(set(values))
            or len(external_refs) > len(set(external_refs))
        ):
            attribute_errors[AttributeInputErrors.DUPLICATED_VALUES].append(
                self.attribute_identifier
            )

        for value_input in multi_values:
            self._validate_selectable_field(
                value_input,
                value_required=self.attribute.value_required,
                attribute_errors=attribute_errors,
            )

    def pre_save_value(self, instance: T_INSTANCE) -> list[tuple]:
        multi_values = self.values_input.multiselect
        if not multi_values:
            return []

        results = []
        values_to_create = []
        pks_to_fetch = []
        ext_refs_to_fetch = []

        for v_input in multi_values:
            if v_input.id:
                _, pk = from_global_id_or_error(v_input.id, "AttributeValue")
                pks_to_fetch.append(pk)
            elif v_input.external_reference and not v_input.value:
                ext_refs_to_fetch.append(v_input.external_reference)
            elif v_input.value:
                values_to_create.append(v_input.value)

        # Fetch existing values by PK and external reference
        existing_values = self.attribute.values.filter(
            Q(pk__in=pks_to_fetch) | Q(external_reference__in=ext_refs_to_fetch)
        )
        results.extend(
            [(AttributeValueBulkActionEnum.NONE, val) for val in existing_values]
        )

        # Prepare new values
        if values_to_create:
            results.extend(
                AttributeAssignmentMixin._prepare_attribute_values(
                    self.attribute, values_to_create
                )
            )

        return results


class FileAttributeHandler(AttributeTypeHandler):
    """Handler for File attribute type."""

    def clean_and_validate(self, attribute_errors: T_ERROR_DICT):
        storage_root_url = get_default_storage_root_url()
        file_url = self.values_input.file_url
        if self.attribute.value_required and not file_url:
            attribute_errors[AttributeInputErrors.FILE_URL_REQUIRED].append(
                self.attribute_identifier
            )
        if file_url and not file_url.startswith(storage_root_url):
            attribute_errors[AttributeInputErrors.INVALID_FILE_URL].append(
                self.attribute_identifier
            )
        self.values_input.file_url = (
            re.sub(storage_root_url, "", file_url) if file_url is not None else file_url
        )

    def pre_save_value(self, instance: T_INSTANCE) -> list[tuple]:
        file_url = self.values_input.file_url
        if not file_url:
            return []

        # File attributes should be unique per assignment, so we create a new value
        # unless this exact URL is already assigned to this instance.
        value = AttributeAssignmentMixin._get_assigned_attribute_value_if_exists(
            instance, self.attribute, "file_url", file_url
        )
        if value:
            return [(AttributeValueBulkActionEnum.NONE, value)]

        name = file_url.split("/")[-1]
        value_obj = AttributeValue(
            attribute=self.attribute,
            file_url=file_url,
            name=name,
            content_type=self.values_input.content_type,
        )
        value_obj.slug = generate_unique_slug(value_obj, name)
        return [(AttributeValueBulkActionEnum.CREATE, value_obj)]


class ReferenceAttributeHandler(AttributeTypeHandler):
    """Handler for Reference attribute type."""

    def clean_and_validate(self, attribute_errors: T_ERROR_DICT):
        """Resolve Graphene IDs and then validate the result.

        Modifies `self.values_input.references` in place.
        """
        references = self.values_input.references

        if not references:
            if self.attribute.value_required:
                attribute_errors[AttributeInputErrors.REFERENCE_REQUIRED].append(
                    self.attribute_identifier
                )
            return

        if not self.attribute.entity_type:
            attribute_errors[AttributeInputErrors.INVALID_INPUT].append(
                self.attribute_identifier
            )
            return
        entity_data = ENTITY_TYPE_MAPPING[self.attribute.entity_type]

        try:
            ref_instances = get_nodes(
                references, self.attribute.entity_type, model=entity_data.model
            )
            self.values_input.references = ref_instances
        except GraphQLError:
            self.values_input.references = []
            attribute_errors[AttributeInputErrors.INVALID_REFERENCE].append(
                self.attribute_identifier
            )

    def pre_save_value(self, instance: T_INSTANCE) -> list[tuple]:
        references = self.values_input.references
        entity_type = self.attribute.entity_type
        if not references or not entity_type:
            return []

        entity_data = ENTITY_TYPE_MAPPING[entity_type]
        results = []
        for ref in references:
            name = getattr(ref, entity_data.name_field)
            if entity_type == AttributeEntityType.PRODUCT_VARIANT:
                name = f"{ref.product.name}: {name}"  # type: ignore[union-attr]

            # Reference values are unique per referenced entity
            slug = slugify(unidecode(f"{instance.id}_{ref.id}"))  # type: ignore[union-attr]
            defaults = {"name": name}
            value_data = {
                "attribute": self.attribute,
                "slug": slug,
                "defaults": defaults,
                entity_data.value_field: ref,
            }
            results.append((AttributeValueBulkActionEnum.GET_OR_CREATE, value_data))
        return results


class PlainTextAttributeHandler(AttributeTypeHandler):
    """Handler for Plain Text attribute type."""

    def clean_and_validate(self, attribute_errors: T_ERROR_DICT):
        if self.attribute.value_required and (
            not self.values_input.plain_text or not self.values_input.plain_text.strip()
        ):
            attribute_errors[AttributeInputErrors.VALUE_REQUIRED].append(
                self.attribute_identifier
            )

    def pre_save_value(self, instance: T_INSTANCE) -> list[tuple]:
        plain_text = self.values_input.plain_text
        if plain_text is None:
            return []

        defaults = {
            "plain_text": plain_text,
            "name": truncatechars(plain_text, 200),
        }
        return self._update_or_create_value(instance, defaults)


class RichTextAttributeHandler(PlainTextAttributeHandler):
    def pre_save_value(self, instance: T_INSTANCE) -> list[tuple]:
        rich_text = self.values_input.rich_text
        if rich_text is None:
            return []

        defaults = {
            "rich_text": rich_text,
            "name": truncatechars(clean_editor_js(rich_text, to_string=True), 200),
        }
        return self._update_or_create_value(instance, defaults)


class NumericAttributeHandler(AttributeTypeHandler):
    def clean_and_validate(self, attribute_errors: T_ERROR_DICT):
        numeric_val = self.values_input.numeric
        if self.attribute.value_required and numeric_val is None:
            attribute_errors[AttributeInputErrors.VALUE_REQUIRED].append(
                self.attribute_identifier
            )
        if numeric_val is not None:
            try:
                float(numeric_val)
            except (ValueError, TypeError):
                attribute_errors[AttributeInputErrors.INVALID_INPUT].append(
                    self.attribute_identifier
                )

    def pre_save_value(self, instance: T_INSTANCE) -> list[tuple]:
        numeric_val = self.values_input.numeric
        if numeric_val is None:
            return []
        defaults = {
            "name": numeric_val,
        }
        return self._update_or_create_value(instance, defaults)


class DateTimeAttributeHandler(AttributeTypeHandler):
    """Handler for Date and DateTime attribute types."""

    def clean_and_validate(self, attribute_errors: T_ERROR_DICT):
        is_date = self.attribute.input_type == AttributeInputType.DATE
        has_value = self.values_input.date if is_date else self.values_input.date_time
        if self.attribute.value_required and not has_value:
            attribute_errors[AttributeInputErrors.VALUE_REQUIRED].append(
                self.attribute_identifier
            )

    def pre_save_value(self, instance: T_INSTANCE) -> list[tuple]:
        is_date = self.attribute.input_type == AttributeInputType.DATE
        value = self.values_input.date if is_date else self.values_input.date_time
        if not value:
            return []

        date_time_val = (
            datetime.datetime.combine(value, datetime.time.min, tzinfo=datetime.UTC)
            if is_date
            else value
        )
        defaults = {"name": str(value), "date_time": date_time_val}
        return self._update_or_create_value(instance, defaults)


class BooleanAttributeHandler(AttributeTypeHandler):
    def clean_and_validate(self, attribute_errors: T_ERROR_DICT):
        if self.attribute.value_required and self.values_input.boolean is None:
            attribute_errors[AttributeInputErrors.VALUE_REQUIRED].append(
                self.attribute_identifier
            )

    def pre_save_value(self, instance: T_INSTANCE) -> list[tuple]:
        boolean_val = self.values_input.boolean
        if boolean_val is None:
            return []

        boolean = bool(boolean_val)
        value = {
            "attribute": self.attribute,
            "slug": slugify(unidecode(f"{self.attribute.id}_{boolean}")),
            "defaults": {
                "name": f"{self.attribute.name}: {'Yes' if boolean else 'No'}",
                "boolean": boolean,
            },
        }
        return [(AttributeValueBulkActionEnum.GET_OR_CREATE, value)]


class LegacyValuesHandler(AttributeTypeHandler):
    """Handler for the deprecated `values: [String!]` field.

    Applicable for Dropdown, Swatch, Multiselect, and Numeric attribute types.
    """

    def clean_and_validate(self, attribute_errors: T_ERROR_DICT):
        """Validate a list of raw string values."""

        values = self.values_input.values or []

        def create_error(error_tuple, message=None):
            msg, code = error_tuple
            return ValidationError(
                message or msg,
                code=getattr(self.error_code_enum, code).value,
                params={"attributes": [self.attr_identifier]},
            )

        # Validation for single-select types
        if (
            self.attribute.input_type not in [AttributeInputType.MULTISELECT]
            and len(values) > 1
        ):
            attribute_errors[AttributeInputErrors.MORE_THAN_ONE_VALUE].append(
                self.attr_identifier
            )

        # Shared validation
        if get_duplicated_values(values):
            attribute_errors[AttributeInputErrors.DUPLICATED_VALUES].append(
                self.attr_identifier
            )

        is_numeric = self.attribute.input_type == AttributeInputType.NUMERIC
        name_field = self.attribute.values.model.name.field

        for value in values:
            if value is None or (not is_numeric and not str(value).strip()):
                attribute_errors[AttributeInputErrors.BLANK_VALUE].append(
                    self.attr_identifier
                )
                continue

            if is_numeric:
                try:
                    float(value)
                except (ValueError, TypeError):
                    attribute_errors[AttributeInputErrors.INVALID_INPUT].append(
                        self.attr_identifier
                    )
            elif name_field.max_length and len(value) > name_field.max_length:
                attribute_errors[AttributeInputErrors.MAX_LENGTH_EXCEEDED].append(
                    self.attr_identifier
                )

    def pre_save_value(self, instance: T_INSTANCE) -> list[tuple]:
        if not self.values_input.values:
            return []

        if self.attribute.input_type == AttributeInputType.NUMERIC:
            value = self.values_input.values[0]
            defaults = {
                "name": value,
            }
            return self._update_or_create_value(instance, defaults)

        return AttributeAssignmentMixin._prepare_attribute_values(
            self.attribute, self.values_input.values
        )


class AttributeAssignmentMixin:
    """Handles cleaning, validation, and saving of attribute data."""

    HANDLER_MAPPING = {
        AttributeInputType.DROPDOWN: SelectableAttributeHandler,
        AttributeInputType.SWATCH: SelectableAttributeHandler,
        AttributeInputType.MULTISELECT: MultiSelectableAttributeHandler,
        AttributeInputType.FILE: FileAttributeHandler,
        AttributeInputType.REFERENCE: ReferenceAttributeHandler,
        AttributeInputType.RICH_TEXT: RichTextAttributeHandler,
        AttributeInputType.PLAIN_TEXT: PlainTextAttributeHandler,
        AttributeInputType.NUMERIC: NumericAttributeHandler,
        AttributeInputType.DATE: DateTimeAttributeHandler,
        AttributeInputType.DATE_TIME: DateTimeAttributeHandler,
        AttributeInputType.BOOLEAN: BooleanAttributeHandler,
    }

    @classmethod
    def _get_assignment_manager_and_fk(cls, instance: T_INSTANCE):
        if isinstance(instance, page_models.Page):
            return attribute_models.AssignedPageAttributeValue.objects, "page_id"
        if isinstance(instance, product_models.Product):
            return attribute_models.AssignedProductAttributeValue.objects, "product_id"
        raise NotImplementedError(
            f"Assignment for {type(instance).__name__} not implemented."
        )

    @classmethod
    def _get_assigned_attribute_value_if_exists(
        cls, instance: T_INSTANCE, attribute: "Attribute", lookup_field: str, value
    ):
        """Unified method to find an existing assigned value."""
        if isinstance(instance, product_models.ProductVariant):
            # variant has old attribute structure so need to handle it differently
            return cls._get_variant_assigned_attribute_value_if_exists(
                instance, attribute, lookup_field, value
            )

        manager, instance_fk = cls._get_assignment_manager_and_fk(instance)
        assigned_values = manager.filter(**{instance_fk: instance.pk})
        return attribute_models.AttributeValue.objects.filter(
            Exists(assigned_values.filter(value_id=OuterRef("id"))),
            attribute_id=attribute.pk,
            **{lookup_field: value},
        ).first()

    @classmethod
    def _get_variant_assigned_attribute_value_if_exists(
        cls, instance: T_INSTANCE, attribute: "Attribute", lookup_field: str, value: str
    ):
        attribute_variant = Exists(
            attribute_models.AttributeVariant.objects.filter(
                pk=OuterRef("assignment_id"),
                attribute_id=attribute.pk,
            )
        )
        assigned_variant = Exists(
            attribute_models.AssignedVariantAttribute.objects.filter(
                attribute_variant
            ).filter(
                # Filter conditions for the main subquery
                variant_id=instance.id,
                values=OuterRef(
                    "pk"
                ),  # Refers to the AttributeValue's pk from the outermost query
            )
        )
        return attribute_models.AttributeValue.objects.filter(
            assigned_variant, **{lookup_field: value}
        ).first()

    @classmethod
    def _resolve_attribute_nodes(
        cls,
        qs: "QuerySet",
        error_class,
        *,
        id_map: dict[int, str],
        ext_ref_set: set[str],
    ):
        """Retrieve attributes nodes from given identifiers."""
        nodes = list(
            qs.filter(Q(pk__in=id_map.keys()) | Q(external_reference__in=ext_ref_set))
        )

        resolved_pks = {node.pk for node in nodes}
        resolved_ext_refs = {node.external_reference for node in nodes}

        missing_pks = [gid for pk, gid in id_map.items() if pk not in resolved_pks]
        missing_ext_refs = list(ext_ref_set - resolved_ext_refs)

        if missing_pks or missing_ext_refs:
            missing = [f"ID: {gid}" for gid in missing_pks] + [
                f"ExtRef: {ref}" for ref in missing_ext_refs
            ]
            raise ValidationError(
                f"Could not resolve attributes: {', '.join(missing)}.",
                code=error_class.NOT_FOUND.value,
            )
        return nodes

    @classmethod
    def clean_input(
        cls,
        raw_input: list[dict],
        attributes_qs: "QuerySet",
        creation: bool = True,
        is_page_attributes: bool = False,
    ) -> T_INPUT_MAP:
        """Resolve, validate, and prepare attribute input."""
        error_class = PageErrorCode if is_page_attributes else ProductErrorCode

        id_map: dict[int, AttrValuesInput] = {}
        ext_ref_map: dict[str, AttrValuesInput] = {}

        for attr_input in raw_input:
            gid = attr_input.pop("id", None)
            ext_ref = attr_input.pop("external_reference", None)

            try:
                validate_one_of_args_is_in_mutation(
                    "id", gid, "external_reference", ext_ref, use_camel_case=True
                )
            except ValidationError as e:
                raise ValidationError(e.message, code=error_class.REQUIRED.value) from e

            values = AttrValuesInput(
                global_id=gid,
                external_reference=ext_ref,
                values=attr_input.pop("values", []),
                file_url=attr_input.pop("file", None),
                **attr_input,
            )
            if gid:
                pk = cls._resolve_attribute_global_id(error_class, gid)
                id_map[int(pk)] = values
            if ext_ref:
                ext_ref_map[ext_ref] = values

        attributes = cls._resolve_attribute_nodes(
            attributes_qs,
            error_class,
            id_map={pk: v.global_id for pk, v in id_map.items()},  # type: ignore[misc]
            ext_ref_set=set(ext_ref_map.keys()),
        )

        cleaned_input = []
        attribute_errors: T_ERROR_DICT = defaultdict(list)
        for attribute in attributes:
            values_input = id_map.get(attribute.pk) or ext_ref_map.get(
                attribute.external_reference
            )
            values_input = cast(AttrValuesInput, values_input)

            is_legacy_path = values_input.values and attribute.input_type in {
                AttributeInputType.DROPDOWN,
                AttributeInputType.MULTISELECT,
                AttributeInputType.SWATCH,
                AttributeInputType.NUMERIC,
            }

            handler_class: type[LegacyValuesHandler | AttributeTypeHandler]
            if is_legacy_path:
                handler_class = LegacyValuesHandler
            else:
                handler_class = cls.HANDLER_MAPPING[attribute.input_type]

            if handler_class:
                handler = handler_class(attribute, values_input, error_class)
                handler.clean_and_validate(attribute_errors)

            cleaned_input.append((attribute, values_input))

        errors = cls.prepare_error_list_from_error_attribute_mapping(
            attribute_errors, error_class
        )

        if creation:
            supplied_pks = {attr.pk for attr, _ in cleaned_input}
            missing_required = attributes_qs.filter(value_required=True).exclude(
                pk__in=supplied_pks
            )
            if missing_required:
                missing_ids = [
                    graphene.Node.to_global_id("Attribute", attr.pk)
                    for attr in missing_required
                ]
                errors.append(
                    ValidationError(
                        "All attributes flagged as having a value required must be supplied.",
                        code=error_class.REQUIRED.value,
                        params={"attributes": missing_ids},
                    )
                )

        if errors:
            raise ValidationError(errors)

        return cleaned_input

    @classmethod
    def _resolve_attribute_global_id(cls, error_class, global_id: str) -> int:
        """Resolve an Attribute global ID into an internal ID (int)."""
        try:
            graphene_type, internal_id = from_global_id_or_error(
                global_id, only_type="Attribute"
            )
        except GraphQLError as e:
            raise ValidationError(str(e), code=error_class.GRAPHQL_ERROR.value) from e
        if not internal_id.isnumeric():
            raise ValidationError(
                f"An invalid ID value was passed: {global_id}",
                code=error_class.INVALID.value,
            )
        return int(internal_id)

    @staticmethod
    def prepare_error_list_from_error_attribute_mapping(
        attribute_errors: T_ERROR_DICT, error_code_enum
    ):
        errors = []
        for error_data, attributes in attribute_errors.items():
            error_msg, error_type = error_data
            error = ValidationError(
                error_msg,
                code=getattr(error_code_enum, error_type).value,
                params={"attributes": attributes},
            )
            errors.append(error)

        return errors

    @classmethod
    def save(cls, instance: T_INSTANCE, cleaned_input: T_INPUT_MAP):
        """Save the cleaned input against the given instance."""
        pre_save_bulk: dict = defaultdict(lambda: defaultdict(list))
        error_class = (
            PageErrorCode
            if isinstance(instance, page_models.Page)
            else ProductErrorCode
        )

        for attribute, values_input in cleaned_input:
            is_legacy_path = values_input.values and attribute.input_type in {
                AttributeInputType.DROPDOWN,
                AttributeInputType.MULTISELECT,
                AttributeInputType.SWATCH,
                AttributeInputType.NUMERIC,
            }

            handler_class: type[AttributeTypeHandler] | None = None
            if is_legacy_path:
                handler_class = LegacyValuesHandler
            else:
                handler_class = cls.HANDLER_MAPPING.get(attribute.input_type)

            if not handler_class:
                continue

            handler = handler_class(attribute, values_input, error_class)
            prepared_values = handler.pre_save_value(instance)

            if not prepared_values:
                pre_save_bulk[AttributeValueBulkActionEnum.NONE].setdefault(
                    attribute, []
                )
            else:
                for action, value_data in prepared_values:
                    pre_save_bulk[action][attribute].append(value_data)

        attribute_and_values = cls._bulk_create_pre_save_values(pre_save_bulk)

        attr_val_map = defaultdict(list)
        clean_assignment_pks = []
        for attribute, values in attribute_and_values.items():
            if not values:
                clean_assignment_pks.append(attribute.pk)
            else:
                attr_val_map[attribute.pk].extend(values)

        associate_attribute_values_to_instance(instance, attr_val_map)

        if clean_assignment_pks:
            values_to_unassign = attribute_models.AttributeValue.objects.filter(
                attribute_id__in=clean_assignment_pks
            )
            # variant has old attribute structure so need to handle it differently
            if isinstance(instance, product_models.ProductVariant):
                cls._clean_variants_assignment(instance, clean_assignment_pks)
                return
            manager, instance_fk = cls._get_assignment_manager_and_fk(instance)
            manager.filter(
                Exists(values_to_unassign.filter(id=OuterRef("value_id"))),
                **{instance_fk: instance.pk},
            ).delete()

    @classmethod
    def _clean_variants_assignment(cls, instance: T_INSTANCE, attribute_ids: list[int]):
        """Unassign attributes from the given instance."""
        attribute_variant = Exists(
            attribute_models.AttributeVariant.objects.filter(
                pk=OuterRef("assignment_id"),
                attribute_id__in=attribute_ids,
            )
        )
        attribute_models.AssignedVariantAttribute.objects.filter(
            attribute_variant
        ).filter(
            variant_id=instance.id,
        ).delete()

    @classmethod
    def _bulk_create_pre_save_values(cls, pre_save_bulk):
        """Execute bulk database operations based on prepared data."""
        results: dict[Attribute, list[AttributeValue]] = defaultdict(list)

        for action, attribute_data in pre_save_bulk.items():
            for attribute, values in attribute_data.items():
                if action == AttributeValueBulkActionEnum.CREATE:
                    values = AttributeValue.objects.bulk_create(values)
                elif action == AttributeValueBulkActionEnum.UPDATE_OR_CREATE:
                    values = AttributeValue.objects.bulk_update_or_create(values)
                elif action == AttributeValueBulkActionEnum.GET_OR_CREATE:
                    values = AttributeValue.objects.bulk_get_or_create(values)
                else:
                    # ensuring that empty values will be added to results,
                    # so assignments will be removed properly in that case
                    results.setdefault(attribute, [])

                results[attribute].extend(values)

        return results

    @classmethod
    def _prepare_attribute_values(
        cls, attribute: "Attribute", values: list[str]
    ) -> list[tuple]:
        slug_to_value_map = {}
        name_to_value_map = {}
        for val in attribute.values.filter(Q(name__in=values) | Q(slug__in=values)):
            slug_to_value_map[val.slug] = val
            name_to_value_map[val.name] = val

        existing_slugs = cls._get_existing_slugs(attribute, values)

        results = []
        for value_str in values:
            slug = slugify(unidecode(value_str))

            # Prioritize matching by slug, then fall back to matching by name.
            value_obj = slug_to_value_map.get(slug) or name_to_value_map.get(value_str)

            if value_obj:
                results.append((AttributeValueBulkActionEnum.NONE, value_obj))
            else:
                # If no existing value is found, prepare a new one for creation.
                unique_slug = prepare_unique_slug(slug, existing_slugs)
                new_value = AttributeValue(
                    attribute=attribute, name=value_str, slug=unique_slug
                )
                results.append((AttributeValueBulkActionEnum.CREATE, new_value))

                # Add the new slug to our set to prevent collisions within this loop.
                existing_slugs.add(unique_slug)

        return results

    @staticmethod
    def _get_existing_slugs(attribute: attribute_models.Attribute, values: list[str]):
        lookup = Q()
        for value in values:
            lookup |= Q(slug__startswith=slugify(unidecode(value)))

        existing_slugs = set(
            attribute.values.filter(lookup).values_list("slug", flat=True)
        )
        return existing_slugs


# TODO: move it
def has_input_modified_attribute_values(
    variant: product_models.ProductVariant, attributes_data: T_INPUT_MAP
) -> bool:
    """Compare already assigned attribute values with values from AttrValuesInput.

    Return:
        `False` if the attribute values are equal, otherwise `True`.

    """
    if variant.product_id is not None:
        assigned_attributes = get_used_attribute_values_for_variant(variant)
        input_attribute_values: defaultdict[str, list[str]] = defaultdict(list)
        for attr, attr_data in attributes_data:
            values = get_values_from_attribute_values_input(attr, attr_data)
            if attr_data.global_id is not None:
                input_attribute_values[attr_data.global_id].extend(values)
        if input_attribute_values != assigned_attributes:
            return True
    return False


def get_values_from_attribute_values_input(
    attribute: attribute_models.Attribute, attribute_data: AttrValuesInput
) -> list[str]:
    """Format attribute values of type FILE."""
    if attribute.input_type == AttributeInputType.FILE:
        return (
            [slugify(attribute_data.file_url.split("/")[-1])]
            if attribute_data.file_url
            else []
        )
    return attribute_data.values or []

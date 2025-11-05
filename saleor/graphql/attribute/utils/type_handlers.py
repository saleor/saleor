import abc
import datetime
import re
from collections.abc import Sequence
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.text import slugify
from graphql.error import GraphQLError
from text_unidecode import unidecode

from ....attribute import AttributeEntityType, AttributeInputType
from ....attribute import models as attribute_models
from ....attribute.models import AttributeValue
from ....core.utils import (
    generate_unique_slug,
    prepare_unique_slug,
)
from ....core.utils.editorjs import clean_editor_js
from ....core.utils.text import safe_truncate
from ....core.utils.url import get_default_storage_root_url
from ...core.utils import from_global_id_or_error, get_duplicated_values
from ...utils import get_nodes
from ..enums import AttributeValueBulkActionEnum
from .shared import (
    ENTITY_TYPE_MAPPING,
    T_ERROR_DICT,
    T_INSTANCE,
    AttrValuesForSelectableFieldInput,
    AttrValuesInput,
    get_assigned_attribute_value_if_exists,
)

if TYPE_CHECKING:
    from ....attribute.models import Attribute


class AttributeInputErrors:
    """Defines error messages and codes for attribute validation."""

    # General Errors
    VALUE_REQUIRED = ("Attribute expects a value but none were given.", "REQUIRED")
    BLANK_VALUE = ("Attribute values cannot be blank.", "REQUIRED")
    DUPLICATED_VALUES = (
        "Duplicated attribute values are provided.",
        "DUPLICATED_INPUT_ITEM",
    )
    INVALID_INPUT = ("Invalid value provided for attribute.", "INVALID")
    MORE_THAN_ONE_VALUE = (
        "Attribute must take only one value.",
        "INVALID",
    )

    ID_AND_VALUE_PROVIDED = (
        "Attribute values cannot be assigned by both id and value.",
        "INVALID",
    )
    ID_AND_EXTERNAL_REFERENCE_PROVIDED = (
        "Attribute values cannot be assigned by both id and external reference",
        "INVALID",
    )
    MAX_LENGTH_EXCEEDED = ("Attribute value length is exceeded.", "INVALID")

    # File Errors
    FILE_URL_REQUIRED = ("A file URL is required for this attribute.", "REQUIRED")
    INVALID_FILE_URL = (
        "The file_url must be the path to the default storage.",
        "INVALID",
    )

    # Reference Errors
    REFERENCE_REQUIRED = ("A reference is required for this attribute.", "REQUIRED")
    INVALID_REFERENCE = ("Invalid reference type.", "INVALID")
    INVALID_REFERENCE_TYPE = (
        "Invalid reference, must be an object from available choices defined by "
        "reference types on attribute.",
        "INVALID",
    )

    # Numeric Errors
    ERROR_NUMERIC_VALUE_REQUIRED = ("Numeric value is required.", "INVALID")


class AttributeTypeHandler(abc.ABC):
    """Abstract base class for attribute type-specific logic."""

    def __init__(
        self,
        attribute: "Attribute",
        values_input: AttrValuesInput,
    ):
        self.attribute = attribute
        self.values_input = values_input
        self.attribute_identifier = (
            values_input.global_id or values_input.external_reference
        )
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

    @classmethod
    def prepare_attribute_values(
        cls, attribute: attribute_models.Attribute, values: list[str]
    ) -> list[tuple]:
        slug_to_value_map = {}
        name_to_value_map = {}
        for val in attribute.values.filter(Q(name__in=values) | Q(slug__in=values)):
            slug_to_value_map[val.slug] = val
            name_to_value_map[val.name] = val

        existing_slugs = cls.get_existing_slugs(attribute, values)

        results = []
        for value_str in values:
            value_obj = slug_to_value_map.get(value_str) or name_to_value_map.get(
                value_str
            )

            if value_obj:
                results.append((AttributeValueBulkActionEnum.NONE, value_obj))
            else:
                # If no existing value is found, prepare a new one for creation.
                unique_slug = prepare_unique_slug(
                    slugify(unidecode(value_str)), existing_slugs
                )
                new_value = AttributeValue(
                    attribute=attribute, name=value_str, slug=unique_slug
                )
                results.append((AttributeValueBulkActionEnum.CREATE, new_value))

                # the set of existing slugs must be updated to not generate
                # accidentally the same slug for two or more values
                existing_slugs.add(unique_slug)

                # extend name to slug value to not create two elements with the same name
                name_to_value_map[new_value.name] = new_value

        return results

    def prepare_attribute_values_with_external_reference(
        self, values: list[tuple[str, str]]
    ) -> list[tuple]:
        existing_slugs = self.get_existing_slugs(self.attribute, [v[1] for v in values])

        results = []
        for ext_ref, value_str in values:
            unique_slug = prepare_unique_slug(
                slugify(unidecode(value_str)), existing_slugs
            )
            new_value = AttributeValue(
                attribute=self.attribute,
                name=value_str,
                slug=unique_slug,
                external_reference=ext_ref,
            )
            results.append((AttributeValueBulkActionEnum.CREATE, new_value))
            existing_slugs.add(unique_slug)

        return results

    @staticmethod
    def get_existing_slugs(attribute: attribute_models.Attribute, values: list[str]):
        lookup = Q()
        for value in values:
            lookup |= Q(slug__startswith=slugify(unidecode(value)))

        existing_slugs = set(
            attribute.values.filter(lookup).values_list("slug", flat=True)
        )
        return existing_slugs


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

        self._validate_selectable_field(
            selectable_input,
            value_required=self.attribute.value_required,
            attribute_errors=attribute_errors,
        )

    def _validate_selectable_field(
        self,
        attr_value_input: AttrValuesForSelectableFieldInput,
        value_required: bool,
        attribute_errors: T_ERROR_DICT,
    ):
        """Validate a single input for a selectable field."""
        id = attr_value_input.id
        value = attr_value_input.value
        external_reference = attr_value_input.external_reference

        if id and external_reference:
            attribute_errors[
                AttributeInputErrors.ID_AND_EXTERNAL_REFERENCE_PROVIDED
            ].append(self.attr_identifier)
            return

        if id and value:
            attribute_errors[AttributeInputErrors.ID_AND_VALUE_PROVIDED].append(
                self.attr_identifier
            )
            return

        if not id and not external_reference and not value and value_required:
            attribute_errors[AttributeInputErrors.VALUE_REQUIRED].append(
                self.attr_identifier
            )
            return

        if value:
            max_length = self.attribute.values.model.name.field.max_length
            if not value.strip():
                attribute_errors[AttributeInputErrors.BLANK_VALUE].append(
                    self.attr_identifier
                )
            elif max_length and len(value) > max_length:
                attribute_errors[AttributeInputErrors.MAX_LENGTH_EXCEEDED].append(
                    self.attr_identifier
                )

        value_identifier = id or external_reference
        if value_identifier:
            if not value_identifier.strip():
                attribute_errors[AttributeInputErrors.BLANK_VALUE].append(
                    self.attr_identifier
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
            return self._parse_external_reference_and_value(ext_ref, value)

        if ext_ref:
            value_instance = attribute_models.AttributeValue.objects.filter(
                external_reference=ext_ref
            ).first()
            if not value_instance:
                raise ValidationError(
                    "Attribute value with given externalReference can't be found"
                )
            return [(AttributeValueBulkActionEnum.NONE, value_instance)]

        if id:
            _, attr_value_id = from_global_id_or_error(id)
            value_instance = attribute_models.AttributeValue.objects.filter(
                pk=attr_value_id
            ).first()
            if not value_instance:
                raise ValidationError("Attribute value with given ID can't be found")
            return [(AttributeValueBulkActionEnum.NONE, value_instance)]

        if value:
            return self.prepare_attribute_values(self.attribute, [value])

        return []

    def _parse_external_reference_and_value(
        self, external_reference: str, attr_value: str | None
    ) -> list[tuple[AttributeValueBulkActionEnum, AttributeValue]]:
        """Get or create an AttributeValue by external reference."""
        value_instance = attribute_models.AttributeValue.objects.filter(
            external_reference=external_reference
        ).first()
        if value_instance:
            if value_instance.name != attr_value:
                raise ValidationError(
                    f"Attribute value with external reference '{external_reference}' already exists "
                    f"with different value '{value_instance.name}'."
                )
            return [
                (
                    AttributeValueBulkActionEnum.NONE,
                    value_instance,
                )
            ]
        if not attr_value:
            raise ValidationError(
                f"Attribute value with given external reference can't be found: {external_reference}"
            )
        return self.prepare_attribute_values_with_external_reference(
            [(external_reference, attr_value or external_reference)]
        )


class MultiSelectableAttributeHandler(SelectableAttributeHandler):
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

        ext_refs = [
            value.external_reference
            for value in multi_values
            if value.external_reference
        ]
        ids = [
            from_global_id_or_error(v_input.id, "AttributeValue")[1]
            for v_input in multi_values
            if v_input.id
        ]
        ext_ref_to_value_map = self.attribute.values.filter(
            external_reference__in=ext_refs
        ).in_bulk(field_name="external_reference")
        id_to_value_map = self.attribute.values.filter(id__in=ids).in_bulk()

        results = []
        values_to_create = []
        external_refs_with_value_to_create = []
        invalid_ids = []
        invalid_ext_refs = []
        invalid_ext_refs_with_current_value = []

        for v_input in multi_values:
            if v_input.id:
                _, pk = from_global_id_or_error(v_input.id, "AttributeValue")
                if value_instance := id_to_value_map.get(int(pk)):
                    results.append((AttributeValueBulkActionEnum.NONE, value_instance))
                else:
                    invalid_ids.append(v_input.id)
            elif v_input.external_reference and not v_input.value:
                if value_instance := ext_ref_to_value_map.get(
                    v_input.external_reference
                ):
                    results.append((AttributeValueBulkActionEnum.NONE, value_instance))
                else:
                    invalid_ext_refs.append(v_input.external_reference)
            elif v_input.external_reference and v_input.value:
                if value_instance := ext_ref_to_value_map.get(
                    v_input.external_reference
                ):
                    if value_instance.name != v_input.value:
                        invalid_ext_refs_with_current_value.append(
                            (v_input.external_reference, value_instance.name)
                        )
                        continue
                    results.append((AttributeValueBulkActionEnum.NONE, value_instance))
                    continue
                external_refs_with_value_to_create.append(
                    (v_input.external_reference, v_input.value)
                )
            elif v_input.value:
                values_to_create.append(v_input.value)

        if invalid_ids:
            raise ValidationError(
                f"Attribute value(s) with given ID(s) can't be found: {', '.join(invalid_ids)}"
            )
        if invalid_ext_refs:
            raise ValidationError(
                f"Attribute value(s) with given external reference(s) can't be found: {', '.join(invalid_ext_refs)}"
            )
        if invalid_ext_refs_with_current_value:
            error_messages = [
                f"Attribute value with external reference '{ext_ref}' already exists with different value '{existing_value}'."
                for ext_ref, existing_value in invalid_ext_refs_with_current_value
            ]
            raise ValidationError("/n".join(error_messages))

        # Prepare new values
        if values_to_create:
            results.extend(
                self.prepare_attribute_values(self.attribute, values_to_create)
            )

        # Prepare new values with external references
        if external_refs_with_value_to_create:
            results.extend(
                self.prepare_attribute_values_with_external_reference(
                    external_refs_with_value_to_create
                )
            )

        return results


class FileAttributeHandler(AttributeTypeHandler):
    """Handler for File attribute type."""

    def clean_and_validate(self, attribute_errors: T_ERROR_DICT):
        storage_root_url = get_default_storage_root_url()
        file_url = self.values_input.file_url
        if self.attribute.value_required and (not file_url or not file_url.strip()):
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
        value = get_assigned_attribute_value_if_exists(
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
    """Handler for Reference and Single Reference attribute type."""

    def get_references(self) -> Sequence[str]:
        if self.attribute.input_type == AttributeInputType.SINGLE_REFERENCE:
            return [self.values_input.reference] if self.values_input.reference else []
        return self.values_input.references or []

    def clean_and_validate(self, attribute_errors: T_ERROR_DICT):
        """Resolve Graphene IDs and then validate the result.

        Modifies `self.values_input.references` in place.
        """
        references = self.get_references()

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

        prefetch_related = (
            ["product"]
            if self.attribute.entity_type == AttributeEntityType.PRODUCT_VARIANT
            else []
        )
        try:
            ref_instances = get_nodes(
                references,
                self.attribute.entity_type,
                model=entity_data.model,
                prefetch_related=prefetch_related,
            )
        except GraphQLError:
            attribute_errors[AttributeInputErrors.INVALID_REFERENCE].append(
                self.attribute_identifier
            )
            return

        invalid_refs = self.get_references_with_invalid_reference_types(
            ref_instances, attribute_errors
        )
        if invalid_refs:
            attribute_errors[AttributeInputErrors.INVALID_REFERENCE_TYPE].append(
                self.attribute_identifier
            )
            return

        self.values_input.reference_objects = ref_instances

    def get_references_with_invalid_reference_types(
        self, ref_instances: list, attribute_errors: T_ERROR_DICT
    ):
        """Validate that all references are of the correct type.

        For `PRODUCT` and `PRODUCT_VARIANT` entity types, check if the
        references belong to the reference product types defined in the attribute.

        For `PAGE` entity type, check if the references belong to the reference page
        types defined in the attribute.
        """
        # `reference_product_types` and `reference_page_types` are pre-fetched
        # in `AttributeAssignmentMixin._resolve_attribute_nodes`
        if reference_product_types := self.attribute.reference_product_types.all():
            ref_product_type_ids = set()
            if self.attribute.entity_type == AttributeEntityType.PRODUCT:
                ref_product_type_ids = {ref.product_type_id for ref in ref_instances}
            elif self.attribute.entity_type == AttributeEntityType.PRODUCT_VARIANT:
                # product is pre-fetched in `get_nodes`
                ref_product_type_ids = {
                    ref.product.product_type_id for ref in ref_instances
                }
            attribute_product_type_ids = {pt.id for pt in reference_product_types}
            invalid_refs = ref_product_type_ids - attribute_product_type_ids
            return invalid_refs
        if reference_page_types := self.attribute.reference_page_types.all():
            ref_page_type_ids = {ref.page_type_id for ref in ref_instances}
            # `reference_page_types` are pre-fetched in `AttributeAssignmentMixin._resolve_attribute_nodes`
            attribute_page_type_ids = {pt.id for pt in reference_page_types}
            invalid_refs = ref_page_type_ids - attribute_page_type_ids
            return invalid_refs
        return {}

    def pre_save_value(self, instance: T_INSTANCE) -> list[tuple]:
        references = self.values_input.reference_objects
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
            slug = slugify(unidecode(f"{instance.id}_{ref.id}"))
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
        plain_text = self.values_input.plain_text
        if self.attribute.value_required and (not plain_text or not plain_text.strip()):
            attribute_errors[AttributeInputErrors.VALUE_REQUIRED].append(
                self.attribute_identifier
            )

    def pre_save_value(self, instance: T_INSTANCE) -> list[tuple]:
        plain_text = self.values_input.plain_text
        if plain_text is None:
            return []

        defaults = {
            "plain_text": plain_text,
            "name": safe_truncate(plain_text, 200),
        }
        return self._update_or_create_value(instance, defaults)


class RichTextAttributeHandler(AttributeTypeHandler):
    """Handler for Rich Text attribute type."""

    def clean_and_validate(self, attribute_errors: T_ERROR_DICT):
        text = clean_editor_js(self.values_input.rich_text or {}, to_string=True)

        if not text.strip() and self.attribute.value_required:
            attribute_errors[AttributeInputErrors.VALUE_REQUIRED].append(
                self.attribute_identifier
            )

    def pre_save_value(self, instance: T_INSTANCE) -> list[tuple]:
        rich_text = self.values_input.rich_text
        if rich_text is None:
            return []

        defaults = {
            "rich_text": rich_text,
            "name": safe_truncate(clean_editor_js(rich_text, to_string=True), 200),
        }
        return self._update_or_create_value(instance, defaults)


class NumericAttributeHandler(AttributeTypeHandler):
    """Handler for Numeric attribute type."""

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
                attribute_errors[
                    AttributeInputErrors.ERROR_NUMERIC_VALUE_REQUIRED
                ].append(self.attribute_identifier)

        if isinstance(numeric_val, bool):
            attribute_errors[AttributeInputErrors.ERROR_NUMERIC_VALUE_REQUIRED].append(
                self.attribute_identifier
            )

    def pre_save_value(self, instance: T_INSTANCE) -> list[tuple]:
        numeric_val = self.values_input.numeric
        if numeric_val is None:
            return []
        defaults = {
            "name": numeric_val,
            "numeric": float(numeric_val),
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
    """Handler for Boolean attribute type."""

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
                "numeric": float(value),
            }
            return self._update_or_create_value(instance, defaults)

        return self.prepare_attribute_values(self.attribute, self.values_input.values)

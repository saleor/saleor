from collections import defaultdict
from typing import TYPE_CHECKING, cast

import graphene
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db.models.expressions import Exists, OuterRef
from graphql.error import GraphQLError

from ....attribute import AttributeInputType
from ....attribute import models as attribute_models
from ....attribute.models import AttributeValue
from ....attribute.utils import associate_attribute_values_to_instance
from ....page.error_codes import PageErrorCode
from ....product import models as product_models
from ....product.error_codes import ProductErrorCode
from ...core.utils import from_global_id_or_error
from ...core.validators import validate_one_of_args_is_in_mutation
from ..enums import AttributeValueBulkActionEnum
from .shared import (
    T_ERROR_DICT,
    T_INSTANCE,
    AttrValuesInput,
    get_assignment_model_and_fk,
)
from .type_handlers import (
    AttributeTypeHandler,
    BooleanAttributeHandler,
    DateTimeAttributeHandler,
    FileAttributeHandler,
    LegacyValuesHandler,
    MultiSelectableAttributeHandler,
    NumericAttributeHandler,
    PlainTextAttributeHandler,
    ReferenceAttributeHandler,
    RichTextAttributeHandler,
    SelectableAttributeHandler,
)

if TYPE_CHECKING:
    from django.db.models import QuerySet


T_INPUT_MAP = list[tuple["attribute_models.Attribute", "AttrValuesInput"]]


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

        id_to_values_input_map, ext_ref_to_values_input_map = (
            cls._prepare_attribute_input_maps(raw_input, error_class)
        )

        attributes = cls._resolve_attribute_nodes(
            attributes_qs,
            error_class,
            id_map={pk: v.global_id for pk, v in id_to_values_input_map.items()},  # type: ignore[misc]
            ext_ref_set=set(ext_ref_to_values_input_map.keys()),
        )

        cleaned_input = cls._validate_and_clean_attributes(
            attributes,
            attributes_qs,
            id_to_values_input_map,
            ext_ref_to_values_input_map,
            error_class,
            creation,
        )

        return cleaned_input

    @classmethod
    def _prepare_attribute_input_maps(
        cls, raw_input: list[dict], error_class
    ) -> tuple[dict[int, AttrValuesInput], dict[str, AttrValuesInput]]:
        """Prepare maps for attribute input based on IDs and external references."""
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

        return id_map, ext_ref_map

    @classmethod
    def _validate_and_clean_attributes(
        cls,
        attributes: list[attribute_models.Attribute],
        attributes_qs: "QuerySet[attribute_models.Attribute]",
        id_to_values_input_map: dict[int, AttrValuesInput],
        ext_ref_to_values_input_map: dict[str, AttrValuesInput],
        error_class,
        creation: bool,
    ) -> T_INPUT_MAP:
        """Validate and clean attribute inputs."""
        cleaned_input = []
        attribute_errors: T_ERROR_DICT = defaultdict(list)

        for attribute in attributes:
            values_input = id_to_values_input_map.get(
                attribute.pk
            ) or ext_ref_to_values_input_map.get(attribute.external_reference)  # type: ignore[arg-type]
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
                handler = handler_class(attribute, values_input)
                handler.clean_and_validate(attribute_errors)

            cleaned_input.append((attribute, values_input))

        errors = cls.prepare_error_list_from_error_attribute_mapping(
            attribute_errors, error_class
        )

        if creation:
            cls._validate_required_attributes(attributes_qs, cleaned_input, errors)

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
    def _validate_required_attributes(
        cls,
        attributes_qs: "QuerySet[attribute_models.Attribute]",
        cleaned_input: T_INPUT_MAP,
        errors: list[ValidationError],
    ):
        """Validate that all required attributes are provided."""
        supplied_pks = {attr.pk for attr, _ in cleaned_input}
        missing_required = attributes_qs.filter(
            Q(value_required=True) & ~Q(pk__in=supplied_pks)
        )
        if missing_required:
            missing_ids = [
                graphene.Node.to_global_id("Attribute", attr.pk)
                for attr in missing_required
            ]
            error = ValidationError(
                "All attributes flagged as having a value required must be supplied.",
                code=ProductErrorCode.REQUIRED.value,
                params={"attributes": missing_ids},
            )
            errors.append(error)

    @classmethod
    def save(cls, instance: T_INSTANCE, cleaned_input: T_INPUT_MAP):
        """Save the cleaned input against the given instance."""
        pre_save_bulk: dict = defaultdict(lambda: defaultdict(list))
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

            handler = handler_class(attribute, values_input)
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

        cls._clean_assignments(instance, clean_assignment_pks)

    @classmethod
    def _clean_assignments(cls, instance: T_INSTANCE, clean_assignment_pks: list[int]):
        """Clean attribute assignments from the given instance."""
        if not clean_assignment_pks:
            return

        values_to_unassign = attribute_models.AttributeValue.objects.filter(
            attribute_id__in=clean_assignment_pks
        )
        # variant has old attribute structure so need to handle it differently
        if isinstance(instance, product_models.ProductVariant):
            cls._clean_variants_assignment(instance, clean_assignment_pks)
            return
        assignment_model, instance_fk = get_assignment_model_and_fk(instance)
        assignment_model.objects.filter(
            Exists(values_to_unassign.filter(id=OuterRef("value_id"))),
            **{instance_fk: instance.pk},
        ).delete()

    @classmethod
    def _clean_variants_assignment(cls, instance: T_INSTANCE, attribute_ids: list[int]):
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
        results: dict[attribute_models.Attribute, list[AttributeValue]] = defaultdict(
            list
        )

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

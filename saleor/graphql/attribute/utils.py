import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Dict, Iterable, List, Optional, Tuple, Union
from urllib.parse import urlparse

import graphene
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.template.defaultfilters import truncatechars
from django.utils import timezone
from django.utils.text import slugify
from graphql.error import GraphQLError

from ...attribute import AttributeEntityType, AttributeInputType, AttributeType
from ...attribute import models as attribute_models
from ...attribute.utils import associate_attribute_values_to_instance
from ...core.utils import generate_unique_slug
from ...core.utils.editorjs import clean_editor_js
from ...page import models as page_models
from ...page.error_codes import PageErrorCode
from ...product import models as product_models
from ...product.error_codes import ProductErrorCode
from ..core.utils import from_global_id_or_error
from ..utils import get_nodes

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from ...attribute.models import Attribute


@dataclass
class AttrValuesInput:
    global_id: str
    values: List[str]
    references: Union[List[str], List[page_models.Page]]
    file_url: Optional[str] = None
    content_type: Optional[str] = None
    rich_text: Optional[dict] = None
    plain_text: Optional[str] = None
    boolean: Optional[bool] = None
    date: Optional[str] = None
    date_time: Optional[str] = None


T_INSTANCE = Union[
    product_models.Product, product_models.ProductVariant, page_models.Page
]
T_INPUT_MAP = List[Tuple[attribute_models.Attribute, AttrValuesInput]]
T_ERROR_DICT = Dict[Tuple[str, str], List[str]]


class AttributeAssignmentMixin:
    """Handles cleaning of the attribute input and creating the proper relations.

    1. You should first call ``clean_input``, to transform and attempt to resolve
       the provided input into actual objects. It will then perform a few
       checks to validate the operations supplied by the user are possible and allowed.
    2. Once everything is ready and all your data is saved inside a transaction,
       you shall call ``save`` with the cleaned input to build all the required
       relations. Once the ``save`` call is done, you are safe from continuing working
       or to commit the transaction.

    Note: you shall never call ``save`` outside of a transaction and never before
    the targeted instance owns a primary key. Failing to do so, the relations will
    be unable to build or might only be partially built.
    """

    REFERENCE_VALUE_NAME_MAPPING = {
        AttributeEntityType.PAGE: "title",
        AttributeEntityType.PRODUCT: "name",
    }

    ENTITY_TYPE_TO_MODEL_MAPPING = {
        AttributeEntityType.PAGE: page_models.Page,
        AttributeEntityType.PRODUCT: product_models.Product,
    }

    @classmethod
    def _resolve_attribute_nodes(
        cls,
        qs: "QuerySet",
        error_class,
        *,
        global_ids: List[str],
        pks: Iterable[int],
        slugs: Iterable[str],
    ):
        """Retrieve attributes nodes from given global IDs and/or slugs."""
        qs = qs.filter(Q(pk__in=pks) | Q(slug__in=slugs))
        nodes: List[attribute_models.Attribute] = list(qs)

        if not nodes:
            raise ValidationError(
                (
                    f"Could not resolve to a node: ids={global_ids}"
                    f" and slugs={list(slugs)}"
                ),
                code=error_class.NOT_FOUND.value,
            )

        nodes_pk_list = set()
        nodes_slug_list = set()
        for node in nodes:
            nodes_pk_list.add(node.pk)
            nodes_slug_list.add(node.slug)

        for pk, global_id in zip(pks, global_ids):
            if pk not in nodes_pk_list:
                raise ValidationError(
                    f"Could not resolve {global_id!r} to Attribute",
                    code=error_class.NOT_FOUND.value,
                )

        for slug in slugs:
            if slug not in nodes_slug_list:
                raise ValidationError(
                    f"Could not resolve slug {slug!r} to Attribute",
                    code=error_class.NOT_FOUND.value,
                )

        return nodes

    @classmethod
    def _resolve_attribute_global_id(cls, error_class, global_id: str) -> int:
        """Resolve an Attribute global ID into an internal ID (int)."""
        try:
            graphene_type, internal_id = from_global_id_or_error(
                global_id, only_type="Attribute"
            )
        except GraphQLError as e:
            raise ValidationError(str(e), code=error_class.GRAPHQL_ERROR.value)
        if not internal_id.isnumeric():
            raise ValidationError(
                f"An invalid ID value was passed: {global_id}",
                code=error_class.INVALID.value,
            )
        return int(internal_id)

    @classmethod
    def _get_assigned_attribute_value_if_exists(
        cls,
        instance: T_INSTANCE,
        attribute: attribute_models.Attribute,
        lookup_field: str,
        value,
    ):
        assignment = instance.attributes.filter(
            assignment__attribute=attribute, **{f"values__{lookup_field}": value}
        ).first()
        return (
            None
            if assignment is None
            else assignment.values.filter(**{lookup_field: value}).first()
        )

    @classmethod
    def clean_input(
        cls,
        raw_input: dict,
        attributes_qs: "QuerySet",
        creation: bool = True,
        is_page_attributes: bool = False,
    ) -> T_INPUT_MAP:
        """Resolve and prepare the input for further checks.

        :param raw_input: The user's attributes input.
        :param attributes_qs:
            A queryset of attributes, the attribute values must be prefetched.
            Prefetch is needed by ``_pre_save_values`` during save.
        :param creation: Whether the input is from creation mutation.
        :param is_page_attributes: Whether the input is for page type or not.

        :raises ValidationError: contain the message.
        :return: The resolved data
        """
        error_class = PageErrorCode if is_page_attributes else ProductErrorCode

        # Mapping to associate the input values back to the resolved attribute nodes
        pks = {}
        slugs = {}

        # Temporary storage of the passed ID for error reporting
        global_ids = []

        for attribute_input in raw_input:
            global_id = attribute_input.get("id")
            slug = attribute_input.get("slug")
            values = AttrValuesInput(
                global_id=global_id,
                values=attribute_input.get("values", []),
                file_url=cls._clean_file_url(attribute_input.get("file")),
                content_type=attribute_input.get("content_type"),
                references=attribute_input.get("references", []),
                rich_text=attribute_input.get("rich_text"),
                plain_text=attribute_input.get("plain_text"),
                boolean=attribute_input.get("boolean"),
                date=attribute_input.get("date"),
                date_time=attribute_input.get("date_time"),
            )

            if global_id:
                internal_id = cls._resolve_attribute_global_id(error_class, global_id)
                global_ids.append(global_id)
                pks[internal_id] = values
            elif slug:
                slugs[slug] = values
            else:
                raise ValidationError(
                    "You must whether supply an ID or a slug",
                    code=error_class.REQUIRED.value,  # type: ignore
                )

        attributes = cls._resolve_attribute_nodes(
            attributes_qs,
            error_class,
            global_ids=global_ids,
            pks=pks.keys(),
            slugs=slugs.keys(),
        )
        attr_with_invalid_references = []
        cleaned_input = []
        for attribute in attributes:
            key = pks.get(attribute.pk, None)

            # Retrieve the primary key by slug if it
            # was not resolved through a global ID but a slug
            if key is None:
                key = slugs[attribute.slug]

            if attribute.input_type == AttributeInputType.REFERENCE:
                try:
                    key = cls._validate_references(error_class, attribute, key)
                except GraphQLError:
                    attr_with_invalid_references.append(attribute)

            cleaned_input.append((attribute, key))

        if attr_with_invalid_references:
            raise ValidationError(
                "Provided references are invalid. Some of the nodes "
                "do not exist or are different types than types defined "
                "in attribute entity type.",
                code=error_class.INVALID.value,  # type: ignore
            )

        cls._validate_attributes_input(
            cleaned_input,
            attributes_qs,
            creation=creation,
            is_page_attributes=is_page_attributes,
        )

        return cleaned_input

    @staticmethod
    def _clean_file_url(file_url: Optional[str]):
        # extract storage path from file URL
        return (
            re.sub(f"^{settings.MEDIA_URL}", "", urlparse(file_url).path)
            if file_url is not None
            else file_url
        )

    @classmethod
    def _validate_references(
        cls, error_class, attribute: attribute_models.Attribute, values: AttrValuesInput
    ) -> AttrValuesInput:
        references = values.references
        if not references:
            return values

        entity_model = cls.ENTITY_TYPE_TO_MODEL_MAPPING[
            attribute.entity_type  # type: ignore
        ]
        try:
            ref_instances = get_nodes(
                references, attribute.entity_type, model=entity_model
            )
            values.references = ref_instances
            return values
        except GraphQLError:
            raise ValidationError("Invalid reference type.", code=error_class.INVALID)

    @classmethod
    def _validate_attributes_input(
        cls,
        cleaned_input: T_INPUT_MAP,
        attribute_qs: "QuerySet",
        *,
        creation: bool,
        is_page_attributes: bool
    ):
        """Check the cleaned attribute input.

        An Attribute queryset is supplied.

        - ensure all required attributes are passed
        - ensure the values are correct

        :raises ValidationError: when an invalid operation was found.
        """
        if errors := validate_attributes_input(
            cleaned_input,
            attribute_qs,
            is_page_attributes=is_page_attributes,
            creation=creation,
        ):
            raise ValidationError(errors)

    @classmethod
    def save(cls, instance: T_INSTANCE, cleaned_input: T_INPUT_MAP):
        """Save the cleaned input into the database against the given instance.

        Note: this should always be ran inside a transaction.

        :param instance: the product or variant to associate the attribute against.
        :param cleaned_input: the cleaned user input (refer to clean_attributes)
        """
        pre_save_methods_mapping = {
            AttributeInputType.FILE: cls._pre_save_file_value,
            AttributeInputType.REFERENCE: cls._pre_save_reference_values,
            AttributeInputType.RICH_TEXT: cls._pre_save_rich_text_values,
            AttributeInputType.PLAIN_TEXT: cls._pre_save_plain_text_values,
            AttributeInputType.NUMERIC: cls._pre_save_numeric_values,
            AttributeInputType.BOOLEAN: cls._pre_save_boolean_values,
            AttributeInputType.DATE: cls._pre_save_date_time_values,
            AttributeInputType.DATE_TIME: cls._pre_save_date_time_values,
        }
        clean_assignment = []
        for attribute, attr_values in cleaned_input:
            if (input_type := attribute.input_type) in pre_save_methods_mapping:
                pre_save_func = pre_save_methods_mapping[input_type]
                attribute_values = pre_save_func(instance, attribute, attr_values)
            else:
                attribute_values = cls._pre_save_values(attribute, attr_values)

            associate_attribute_values_to_instance(
                instance, attribute, *attribute_values
            )
            if not attribute_values:
                clean_assignment.append(attribute.pk)

        # drop attribute assignment model when values are unassigned from instance
        if clean_assignment:
            instance.attributes.filter(
                assignment__attribute_id__in=clean_assignment
            ).delete()

    @classmethod
    def _pre_save_values(
        cls, attribute: attribute_models.Attribute, attr_values: AttrValuesInput
    ):
        """Lazy-retrieve or create the database objects from the supplied raw values."""
        get_or_create = attribute.values.get_or_create

        if not attr_values.values:
            return tuple()

        return tuple(
            get_or_create(
                attribute=attribute,
                slug=slugify(value, allow_unicode=True),
                defaults={"name": value},
            )[0]
            for value in attr_values.values
        )

    @classmethod
    def _pre_save_numeric_values(
        cls,
        instance: T_INSTANCE,
        attribute: attribute_models.Attribute,
        attr_values: AttrValuesInput,
    ):
        if not attr_values.values:
            return tuple()
        defaults = {
            "name": attr_values.values[0],
        }
        return cls._update_or_create_value(instance, attribute, defaults)

    @classmethod
    def _pre_save_rich_text_values(
        cls,
        instance: T_INSTANCE,
        attribute: attribute_models.Attribute,
        attr_values: AttrValuesInput,
    ):
        if not attr_values.rich_text:
            return tuple()
        defaults = {
            "rich_text": attr_values.rich_text,
            "name": truncatechars(
                clean_editor_js(attr_values.rich_text, to_string=True), 200
            ),
        }
        return cls._update_or_create_value(instance, attribute, defaults)

    @classmethod
    def _pre_save_plain_text_values(
        cls,
        instance: T_INSTANCE,
        attribute: attribute_models.Attribute,
        attr_values: AttrValuesInput,
    ):
        if not attr_values.plain_text:
            return tuple()
        defaults = {
            "plain_text": attr_values.plain_text,
            "name": truncatechars(attr_values.plain_text, 200),
        }
        return cls._update_or_create_value(instance, attribute, defaults)

    @classmethod
    def _pre_save_boolean_values(
        cls,
        instance: T_INSTANCE,
        attribute: attribute_models.Attribute,
        attr_values: AttrValuesInput,
    ):
        if attr_values.boolean is None:
            return tuple()
        get_or_create = attribute.values.get_or_create
        boolean = bool(attr_values.boolean)
        value, _ = get_or_create(
            attribute=attribute,
            slug=slugify(f"{attribute.id}_{boolean}", allow_unicode=True),
            defaults={
                "name": f"{attribute.name}: {'Yes' if boolean else 'No'}",
                "boolean": boolean,
            },
        )
        return (value,)

    @classmethod
    def _pre_save_date_time_values(
        cls,
        instance: T_INSTANCE,
        attribute: attribute_models.Attribute,
        attr_values: AttrValuesInput,
    ):
        is_date_attr = attribute.input_type == AttributeInputType.DATE
        value = attr_values.date if is_date_attr else attr_values.date_time

        if value is None:
            return tuple()

        tz = timezone.get_current_timezone()
        date_time = (
            datetime(
                value.year, value.month, value.day, 0, 0, tzinfo=tz  # type: ignore
            )
            if is_date_attr
            else value
        )
        defaults = {"name": value, "date_time": date_time}
        return (
            cls._update_or_create_value(instance, attribute, defaults) if value else ()
        )

    @classmethod
    def _update_or_create_value(
        cls,
        instance: T_INSTANCE,
        attribute: attribute_models.Attribute,
        value_defaults: dict,
    ):
        update_or_create = attribute.values.update_or_create
        slug = slugify(f"{instance.id}_{attribute.id}", allow_unicode=True)
        value, _created = update_or_create(
            attribute=attribute,
            slug=slug,
            defaults=value_defaults,
        )
        return (value,)

    @classmethod
    def _pre_save_reference_values(
        cls,
        instance,
        attribute: attribute_models.Attribute,
        attr_values: AttrValuesInput,
    ):
        """Lazy-retrieve or create the database objects from the supplied raw values.

        Slug value is generated based on instance and reference entity id.
        """
        if not attr_values.references:
            return tuple()

        field_name = cls.REFERENCE_VALUE_NAME_MAPPING[
            attribute.entity_type  # type: ignore
        ]
        get_or_create = attribute.values.get_or_create

        reference_list = []
        for ref in attr_values.references:
            reference_page = None
            reference_product = None

            if attribute.entity_type == AttributeEntityType.PAGE:
                reference_page = ref
            else:
                reference_product = ref

            reference_list.append(
                get_or_create(
                    attribute=attribute,
                    reference_product=reference_product,
                    reference_page=reference_page,
                    slug=slugify(
                        f"{instance.id}_{ref.id}",  # type: ignore
                        allow_unicode=True,
                    ),
                    defaults={"name": getattr(ref, field_name)},
                )[0]
            )
        return tuple(reference_list)

    @classmethod
    def _pre_save_file_value(
        cls,
        instance: T_INSTANCE,
        attribute: attribute_models.Attribute,
        attr_value: AttrValuesInput,
    ):
        """Create database file attribute value object from the supplied value.

        For every URL new value must be created as file attribute can be removed
        separately from every instance.
        """
        file_url = attr_value.file_url
        if not file_url:
            return tuple()
        name = file_url.split("/")[-1]
        # don't create new value when assignment already exists
        value = cls._get_assigned_attribute_value_if_exists(
            instance, attribute, "file_url", attr_value.file_url
        )
        if value is None:
            value = attribute_models.AttributeValue(
                attribute=attribute,
                file_url=file_url,
                name=name,
                content_type=attr_value.content_type,
            )
            value.slug = generate_unique_slug(value, name)  # type: ignore
            value.save()
        return (value,)


def get_variant_selection_attributes(qs: "QuerySet") -> "QuerySet":
    return qs.filter(
        type=AttributeType.PRODUCT_TYPE, attributevariant__variant_selection=True
    )


class AttributeInputErrors:
    """Define error message and error code for given error.

    All used error codes must be specified in PageErrorCode and ProductErrorCode.
    """

    ERROR_NO_VALUE_GIVEN = (
        "Attribute expects a value but none were given.",
        "REQUIRED",
    )
    ERROR_MORE_THAN_ONE_VALUE_GIVEN = (
        "Attribute must take only one value.",
        "INVALID",
    )
    ERROR_BLANK_VALUE = (
        "Attribute values cannot be blank.",
        "REQUIRED",
    )

    # file errors
    ERROR_NO_FILE_GIVEN = (
        "Attribute file url cannot be blank.",
        "REQUIRED",
    )
    ERROR_BLANK_FILE_VALUE = (
        "Attribute expects a file url but none were given.",
        "REQUIRED",
    )

    # reference errors
    ERROR_NO_REFERENCE_GIVEN = (
        "Attribute expects an reference but none were given.",
        "REQUIRED",
    )

    # numeric errors
    ERROR_NUMERIC_VALUE_REQUIRED = (
        "Numeric value is required.",
        "INVALID",
    )

    # text errors
    ERROR_MAX_LENGTH = (
        "Attribute value length is exceeded.",
        "INVALID",
    )


def validate_attributes_input(
    input_data: List[Tuple["Attribute", "AttrValuesInput"]],
    attribute_qs: "QuerySet",
    *,
    is_page_attributes: bool,
    creation: bool,
):
    """Validate attribute input.

    - ensure all required attributes are passed
    - ensure the values are correct for a products or a page
    """

    error_code_enum = PageErrorCode if is_page_attributes else ProductErrorCode
    attribute_errors: T_ERROR_DICT = defaultdict(list)
    for attribute, attr_values in input_data:
        attrs = (
            attribute,
            attr_values,
            attribute_errors,
        )
        input_type_to_validation_func_mapping = {
            AttributeInputType.FILE: validate_file_attributes_input,
            AttributeInputType.REFERENCE: validate_reference_attributes_input,
            AttributeInputType.RICH_TEXT: validate_rich_text_attributes_input,
            AttributeInputType.PLAIN_TEXT: validate_plain_text_attributes_input,
            AttributeInputType.BOOLEAN: validate_boolean_input,
            AttributeInputType.DATE: validate_date_time_input,
            AttributeInputType.DATE_TIME: validate_date_time_input,
        }
        if validation_func := input_type_to_validation_func_mapping.get(
            attribute.input_type
        ):
            validation_func(*attrs)
        # validation for other input types
        else:
            validate_standard_attributes_input(*attrs)

    errors = prepare_error_list_from_error_attribute_mapping(
        attribute_errors, error_code_enum
    )
    # Check if all required attributes are in input only when instance is created.
    # We should allow updating any instance attributes.
    if creation:
        errors = validate_required_attributes(
            input_data, attribute_qs, errors, error_code_enum
        )

    return errors


def validate_file_attributes_input(
    attribute: "Attribute",
    attr_values: "AttrValuesInput",
    attribute_errors: T_ERROR_DICT,
):
    attribute_id = attr_values.global_id
    value = attr_values.file_url
    if not value:
        if attribute.value_required:
            attribute_errors[AttributeInputErrors.ERROR_NO_FILE_GIVEN].append(
                attribute_id
            )
    elif not value.strip():
        attribute_errors[AttributeInputErrors.ERROR_BLANK_FILE_VALUE].append(
            attribute_id
        )


def validate_reference_attributes_input(
    attribute: "Attribute",
    attr_values: "AttrValuesInput",
    attribute_errors: T_ERROR_DICT,
):
    attribute_id = attr_values.global_id
    references = attr_values.references
    if not references:
        if attribute.value_required:
            attribute_errors[AttributeInputErrors.ERROR_NO_REFERENCE_GIVEN].append(
                attribute_id
            )


def validate_boolean_input(
    attribute: "Attribute",
    attr_values: "AttrValuesInput",
    attribute_errors: T_ERROR_DICT,
):
    attribute_id = attr_values.global_id
    value = attr_values.boolean

    if attribute.value_required and value is None:
        attribute_errors[AttributeInputErrors.ERROR_BLANK_VALUE].append(attribute_id)


def validate_rich_text_attributes_input(
    attribute: "Attribute",
    attr_values: "AttrValuesInput",
    attribute_errors: T_ERROR_DICT,
):
    attribute_id = attr_values.global_id
    text = clean_editor_js(attr_values.rich_text or {}, to_string=True)

    if not text.strip() and attribute.value_required:
        attribute_errors[AttributeInputErrors.ERROR_NO_VALUE_GIVEN].append(attribute_id)


def validate_plain_text_attributes_input(
    attribute: "Attribute",
    attr_values: "AttrValuesInput",
    attribute_errors: T_ERROR_DICT,
):
    attribute_id = attr_values.global_id

    if (
        not attr_values.plain_text or not attr_values.plain_text.strip()
    ) and attribute.value_required:
        attribute_errors[AttributeInputErrors.ERROR_NO_VALUE_GIVEN].append(attribute_id)


def validate_standard_attributes_input(
    attribute: "Attribute",
    attr_values: "AttrValuesInput",
    attribute_errors: T_ERROR_DICT,
):
    attribute_id = attr_values.global_id

    if not attr_values.values:
        if attribute.value_required:
            attribute_errors[AttributeInputErrors.ERROR_NO_VALUE_GIVEN].append(
                attribute_id
            )
    elif (
        attribute.input_type != AttributeInputType.MULTISELECT
        and len(attr_values.values) != 1
    ):
        attribute_errors[AttributeInputErrors.ERROR_MORE_THAN_ONE_VALUE_GIVEN].append(
            attribute_id
        )

    validate_values(
        attribute_id,
        attribute,
        attr_values.values,
        attribute_errors,
    )


def validate_date_time_input(
    attribute: "Attribute",
    attr_values: "AttrValuesInput",
    attribute_errors: T_ERROR_DICT,
):
    is_blank_date = (
        attribute.input_type == AttributeInputType.DATE and not attr_values.date
    )
    is_blank_date_time = (
        attribute.input_type == AttributeInputType.DATE_TIME
        and not attr_values.date_time
    )

    if attribute.value_required and (is_blank_date or is_blank_date_time):
        attribute_errors[AttributeInputErrors.ERROR_NO_VALUE_GIVEN].append(
            attr_values.global_id
        )


def validate_values(
    attribute_id: str,
    attribute: "Attribute",
    values: list,
    attribute_errors: T_ERROR_DICT,
):
    name_field = attribute.values.model.name.field  # type: ignore
    is_numeric = attribute.input_type == AttributeInputType.NUMERIC
    for value in values:
        if value is None or (not is_numeric and not value.strip()):
            attribute_errors[AttributeInputErrors.ERROR_BLANK_VALUE].append(
                attribute_id
            )
        elif is_numeric:
            try:
                float(value)
            except ValueError:
                attribute_errors[
                    AttributeInputErrors.ERROR_NUMERIC_VALUE_REQUIRED
                ].append(attribute_id)
        elif len(value) > name_field.max_length:
            attribute_errors[AttributeInputErrors.ERROR_MAX_LENGTH].append(attribute_id)


def validate_required_attributes(
    input_data: List[Tuple["Attribute", "AttrValuesInput"]],
    attribute_qs: "QuerySet",
    errors: List[ValidationError],
    error_code_enum,
):
    """Ensure all required attributes are supplied."""

    supplied_attribute_pk = [attribute.pk for attribute, _ in input_data]

    missing_required_attributes = attribute_qs.filter(
        Q(value_required=True) & ~Q(pk__in=supplied_attribute_pk)
    )

    if missing_required_attributes:
        ids = [
            graphene.Node.to_global_id("Attribute", attr.pk)
            for attr in missing_required_attributes
        ]
        error = ValidationError(
            "All attributes flagged as having a value required must be supplied.",
            code=error_code_enum.REQUIRED.value,  # type: ignore
            params={"attributes": ids},
        )
        errors.append(error)

    return errors


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

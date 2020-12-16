from collections import defaultdict, namedtuple
from typing import TYPE_CHECKING, Dict, Iterable, List, Tuple, Union

import graphene
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.text import slugify
from graphql_relay import from_global_id

from ...attribute import AttributeInputType, AttributeType, models as attribute_models
from ...attribute.utils import associate_attribute_values_to_instance
from ...core.utils import generate_unique_slug
from ...page import models as page_models
from ...page.error_codes import PageErrorCode
from ...product import models as product_models
from ...product.error_codes import ProductErrorCode

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from ...attribute.models import Attribute


AttrValuesInput = namedtuple(
    "AttrValuesInput", ["global_id", "values", "file_url", "content_type"]
)
T_INSTANCE = Union[
    product_models.Product, product_models.ProductVariant, page_models.Page
]
T_INPUT_MAP = List[Tuple[attribute_models.Attribute, AttrValuesInput]]


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

    @classmethod
    def _resolve_attribute_nodes(
        cls,
        qs: "QuerySet",
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
                code=ProductErrorCode.NOT_FOUND.value,
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
                    code=ProductErrorCode.NOT_FOUND.value,
                )

        for slug in slugs:
            if slug not in nodes_slug_list:
                raise ValidationError(
                    f"Could not resolve slug {slug!r} to Attribute",
                    code=ProductErrorCode.NOT_FOUND.value,
                )

        return nodes

    @classmethod
    def _resolve_attribute_global_id(cls, global_id: str) -> int:
        """Resolve an Attribute global ID into an internal ID (int)."""
        graphene_type, internal_id = from_global_id(global_id)  # type: str, str
        if graphene_type != "Attribute":
            raise ValidationError(
                f"Must receive an Attribute id, got {graphene_type}.",
                code=ProductErrorCode.INVALID.value,
            )
        if not internal_id.isnumeric():
            raise ValidationError(
                f"An invalid ID value was passed: {global_id}",
                code=ProductErrorCode.INVALID.value,
            )
        return int(internal_id)

    @classmethod
    def _pre_save_values(
        cls, attribute: attribute_models.Attribute, attr_values: AttrValuesInput
    ):
        """Lazy-retrieve or create the database objects from the supplied raw values."""
        get_or_create = attribute.values.get_or_create
        return tuple(
            get_or_create(
                attribute=attribute,
                slug=slugify(value, allow_unicode=True),
                defaults={"name": value},
            )[0]
            for value in attr_values.values
        )

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
        # don't create ne value when assignment already exists
        value = cls._get_assigned_attribute_value_if_exists(
            instance, attribute, attr_value.file_url
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

    @classmethod
    def _get_assigned_attribute_value_if_exists(
        cls, instance: T_INSTANCE, attribute: attribute_models.Attribute, file_url
    ):
        assignment = instance.attributes.filter(
            assignment__attribute=attribute, values__file_url=file_url
        ).first()
        return (
            None
            if assignment is None
            else assignment.values.filter(file_url=file_url).first()
        )

    @classmethod
    def _validate_attributes_input(
        cls,
        cleaned_input: T_INPUT_MAP,
        attribute_qs: "QuerySet",
        *,
        is_variant: bool,
        is_page_attributes: bool
    ):
        """Check the cleaned attribute input.

        An Attribute queryset is supplied.

        - ensure all required attributes are passed
        - ensure the values are correct

        :raises ValidationError: when an invalid operation was found.
        """
        variant_validation = False
        if is_variant:
            qs = get_variant_selection_attributes(attribute_qs)
            if len(cleaned_input) < qs.count():
                raise ValidationError(
                    "All variant selection attributes must take a value.",
                    code=ProductErrorCode.REQUIRED.value,
                )
            variant_validation = True

        errors = validate_attributes_input(
            cleaned_input,
            attribute_qs,
            is_page_attributes=is_page_attributes,
            variant_validation=variant_validation,
        )

        if errors:
            raise ValidationError(errors)

    @classmethod
    def clean_input(
        cls,
        raw_input: dict,
        attributes_qs: "QuerySet",
        is_variant: bool = False,
        is_page_attributes: bool = False,
    ) -> T_INPUT_MAP:
        """Resolve and prepare the input for further checks.

        :param raw_input: The user's attributes input.
        :param attributes_qs:
            A queryset of attributes, the attribute values must be prefetched.
            Prefetch is needed by ``_pre_save_values`` during save.
        :param page_attributes: Whether the input is for page type or not.
        :param is_variant: Whether the input is for a variant or a product.

        :raises ValidationError: contain the message.
        :return: The resolved data
        """

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
                file_url=attribute_input.get("file"),
                content_type=attribute_input.get("content_type"),
            )

            if global_id:
                internal_id = cls._resolve_attribute_global_id(global_id)
                global_ids.append(global_id)
                pks[internal_id] = values
            elif slug:
                slugs[slug] = values
            else:
                raise ValidationError(
                    "You must whether supply an ID or a slug",
                    code=ProductErrorCode.REQUIRED.value,
                )

        attributes = cls._resolve_attribute_nodes(
            attributes_qs, global_ids=global_ids, pks=pks.keys(), slugs=slugs.keys()
        )
        cleaned_input = []
        for attribute in attributes:
            key = pks.get(attribute.pk, None)

            # Retrieve the primary key by slug if it
            # was not resolved through a global ID but a slug
            if key is None:
                key = slugs[attribute.slug]

            cleaned_input.append((attribute, key))
        cls._validate_attributes_input(
            cleaned_input,
            attributes_qs,
            is_variant=is_variant,
            is_page_attributes=is_page_attributes,
        )

        return cleaned_input

    @classmethod
    def save(cls, instance: T_INSTANCE, cleaned_input: T_INPUT_MAP):
        """Save the cleaned input into the database against the given instance.

        Note: this should always be ran inside a transaction.

        :param instance: the product or variant to associate the attribute against.
        :param cleaned_input: the cleaned user input (refer to clean_attributes)
        """
        for attribute, attr_values in cleaned_input:
            if attribute.input_type == AttributeInputType.FILE:
                attribute_values = cls._pre_save_file_value(
                    instance, attribute, attr_values
                )
            else:
                attribute_values = cls._pre_save_values(attribute, attr_values)
            associate_attribute_values_to_instance(
                instance, attribute, *attribute_values
            )


def get_variant_selection_attributes(qs: "QuerySet"):
    return qs.filter(
        input_type__in=AttributeInputType.ALLOWED_IN_VARIANT_SELECTION,
        type=AttributeType.PRODUCT_TYPE,
    )


class ProductAttributeInputErrors:
    ERROR_NO_VALUE_GIVEN = ValidationError(
        "Attribute expects a value but none were given",
        code=PageErrorCode.REQUIRED.value,
    )
    ERROR_DROPDOWN_GET_MORE_THAN_ONE_VALUE = ValidationError(
        "Attribute must take only one value", code=PageErrorCode.INVALID.value,
    )
    ERROR_BLANK_VALUE = ValidationError(
        "Attribute values cannot be blank", code=PageErrorCode.REQUIRED.value,
    )

    # file errors
    ERROR_NO_FILE_GIVEN = ValidationError(
        "Attribute file url cannot be blank", code=PageErrorCode.REQUIRED.value,
    )
    ERROR_BLANK_FILE_VALUE = ValidationError(
        "Attribute expects a file url but none were given",
        code=PageErrorCode.REQUIRED.value,
    )


class PageAttributeInputErrors:
    ERROR_NO_VALUE_GIVEN = ValidationError(
        "Attribute expects a value but none were given",
        code=ProductErrorCode.REQUIRED.value,
    )
    ERROR_DROPDOWN_GET_MORE_THAN_ONE_VALUE = ValidationError(
        "Attribute must take only one value", code=ProductErrorCode.INVALID.value,
    )
    ERROR_BLANK_VALUE = ValidationError(
        "Attribute values cannot be blank", code=ProductErrorCode.REQUIRED.value,
    )

    # file errors
    ERROR_NO_FILE_GIVEN = ValidationError(
        "Attribute file url cannot be blank", code=ProductErrorCode.REQUIRED.value,
    )
    ERROR_BLANK_FILE_VALUE = ValidationError(
        "Attribute expects a file url but none were given",
        code=ProductErrorCode.REQUIRED.value,
    )


def validate_attributes_input(
    input_data: List[Tuple["Attribute", "AttrValuesInput"]],
    attribute_qs: "QuerySet",
    *,
    is_page_attributes: bool,
    variant_validation: bool,
):
    """Validate attribute input.

    - ensure all required attributes are passed
    - ensure the values are correct for a products or a page
    """

    errors_data_structure = (
        PageAttributeInputErrors if is_page_attributes else ProductAttributeInputErrors
    )
    attribute_errors: Dict[ValidationError, List[str]] = defaultdict(list)
    for attribute, attr_values in input_data:
        # validation for file attribute
        if attribute.input_type == AttributeInputType.FILE:
            validate_file_attributes_input(
                attribute,
                attr_values,
                errors_data_structure,
                attribute_errors,
                variant_validation,
            )
        # validation for other input types
        else:
            validate_not_file_attributes_input(
                attribute,
                attr_values,
                errors_data_structure,
                attribute_errors,
                variant_validation,
            )

    errors = prepare_error_list_from_error_attribute_mapping(attribute_errors)
    if not variant_validation:
        errors = validate_required_attributes(
            input_data, attribute_qs, errors, is_page_attributes
        )

    return errors


def validate_file_attributes_input(
    attribute: "Attribute",
    attr_values: "AttrValuesInput",
    errors_data_structure,
    attribute_errors: Dict[ValidationError, List[str]],
    variant_validation: bool,
):
    attribute_id = attr_values.global_id
    value = attr_values.file_url
    if not value:
        if attribute.value_required or (
            variant_validation and is_variant_selection_attribute(attribute)
        ):
            attribute_errors[errors_data_structure.ERROR_NO_FILE_GIVEN].append(
                attribute_id
            )
    elif not value.strip():
        attribute_errors[errors_data_structure.ERROR_BLANK_FILE_VALUE].append(
            attribute_id
        )


def validate_not_file_attributes_input(
    attribute: "Attribute",
    attr_values: "AttrValuesInput",
    errors_data_structure,
    attribute_errors: Dict[ValidationError, List[str]],
    variant_validation: bool,
):
    attribute_id = attr_values.global_id
    if not attr_values.values:
        if attribute.value_required or (
            variant_validation and is_variant_selection_attribute(attribute)
        ):
            attribute_errors[errors_data_structure.ERROR_NO_VALUE_GIVEN].append(
                attribute_id
            )
    elif (
        attribute.input_type != AttributeInputType.MULTISELECT
        and len(attr_values.values) != 1
    ):
        attribute_errors[
            errors_data_structure.ERROR_DROPDOWN_GET_MORE_THAN_ONE_VALUE
        ].append(attribute_id)
    for value in attr_values.values:
        if value is None or not value.strip():
            attribute_errors[errors_data_structure.ERROR_BLANK_VALUE].append(
                attribute_id
            )


def is_variant_selection_attribute(attribute: attribute_models.Attribute):
    return attribute.input_type in AttributeInputType.ALLOWED_IN_VARIANT_SELECTION


def validate_required_attributes(
    input_data: List[Tuple["Attribute", "AttrValuesInput"]],
    attribute_qs: "QuerySet",
    errors: List[ValidationError],
    is_page_attributes: bool,
):
    """Ensure all required attributes are supplied."""

    supplied_attribute_pk = [attribute.pk for attribute, _ in input_data]
    error_code_enum = PageErrorCode if is_page_attributes else ProductErrorCode

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
    attribute_errors: Dict[ValidationError, List[str]]
):
    errors = []
    for error, attributes in attribute_errors.items():
        error.params = {"attributes": attributes}
        errors.append(error)

    return errors

from typing import TYPE_CHECKING, Iterable, List, Optional, Tuple, Union

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.text import slugify
from graphql.error import GraphQLError
from graphql_relay import from_global_id

from ....attribute import AttributeEntityType, AttributeInputType
from ....attribute import models as attribute_models
from ....attribute.utils import associate_attribute_values_to_instance
from ....core.utils import generate_unique_slug
from ....page import models as page_models
from ....page.error_codes import PageErrorCode
from ....product import models as product_models
from ....product.error_codes import ProductErrorCode
from ...utils import get_nodes
from . import AttrValuesInput, get_variant_selection_attributes
from .validators import validate_attributes_input

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from ....site.models import SiteSettings


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

    REFERENCE_VALUE_NAME_MAPPING = {
        AttributeEntityType.PAGE: "title",
        AttributeEntityType.PRODUCT: "name",
    }

    ENTITY_TYPE_TO_MODEL_MAPPING = {
        AttributeEntityType.PAGE: page_models.Page,
        AttributeEntityType.PRODUCT: product_models.Product,
    }

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
                file_url=attribute_input.get("file"),
                content_type=attribute_input.get("content_type"),
                references=attribute_input.get("references", []),
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
                    key = cls._validate_references(attribute, key)
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
            is_variant=is_variant,
            is_page_attributes=is_page_attributes,
        )

        return cleaned_input

    @classmethod
    def _resolve_attribute_global_id(cls, error_class, global_id: str) -> int:
        """Resolve an Attribute global ID into an internal ID (int)."""
        graphene_type, internal_id = from_global_id(global_id)  # type: str, str
        if graphene_type != "Attribute":
            raise ValidationError(
                f"Must receive an Attribute id, got {graphene_type}.",
                code=error_class.INVALID.value,
            )
        if not internal_id.isnumeric():
            raise ValidationError(
                f"An invalid ID value was passed: {global_id}",
                code=error_class.INVALID.value,
            )
        return int(internal_id)

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
    def _validate_references(
        cls, attribute: attribute_models.Attribute, values: AttrValuesInput
    ) -> AttrValuesInput:
        references = values.references
        if not references:
            return values

        entity_model = cls.ENTITY_TYPE_TO_MODEL_MAPPING[
            attribute.entity_type  # type: ignore
        ]
        ref_instances = get_nodes(references, attribute.entity_type, model=entity_model)
        values.references = ref_instances
        return values

    @staticmethod
    def _validate_attributes_input(
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
    def save(
        cls,
        instance: T_INSTANCE,
        cleaned_input: T_INPUT_MAP,
        site_settings: Optional["SiteSettings"] = None,
    ):
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
            elif attribute.input_type == AttributeInputType.REFERENCE:
                attribute_values = cls._pre_save_reference_values(
                    instance, attribute, attr_values
                )
            else:
                attribute_values = cls._pre_save_values(attribute, attr_values)
            associate_attribute_values_to_instance(
                instance, attribute, attribute_values, site_settings
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

    @staticmethod
    def _get_assigned_attribute_value_if_exists(
        instance: T_INSTANCE, attribute: attribute_models.Attribute, file_url
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
    def _pre_save_reference_values(
        cls,
        instance,
        attribute: attribute_models.Attribute,
        attr_values: AttrValuesInput,
    ):
        """Lazy-retrieve or create the database objects from the supplied raw values.

        Slug value is generated based on instance and reference entity id.
        """
        field_name = cls.REFERENCE_VALUE_NAME_MAPPING[
            attribute.entity_type  # type: ignore
        ]
        get_or_create = attribute.values.get_or_create
        return tuple(
            get_or_create(
                attribute=attribute,
                slug=slugify(
                    f"{instance.id}_{reference.id}",  # type: ignore
                    allow_unicode=True,
                ),
                defaults={"name": getattr(reference, field_name)},
            )[0]
            for reference in attr_values.references
        )

    @staticmethod
    def _pre_save_values(
        attribute: attribute_models.Attribute, attr_values: AttrValuesInput
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

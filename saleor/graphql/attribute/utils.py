import datetime
import re
from collections import defaultdict, namedtuple
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union

import graphene
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db.models.expressions import Exists, OuterRef
from django.template.defaultfilters import truncatechars
from django.utils import timezone
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
from ..utils import get_nodes
from .enums import AttributeValueBulkActionEnum

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from ...attribute.models import Attribute


@dataclass
class AttrValuesForSelectableFieldInput:
    id: Optional[str] = None
    external_reference: Optional[str] = None
    value: Optional[str] = None


@dataclass
class AttrValuesInput:
    global_id: Optional[str] = None
    external_reference: Optional[str] = None
    values: Optional[list[str]] = None
    dropdown: Optional[AttrValuesForSelectableFieldInput] = None
    swatch: Optional[AttrValuesForSelectableFieldInput] = None
    multiselect: Optional[list[AttrValuesForSelectableFieldInput]] = None
    numeric: Optional[str] = None
    references: Union[list[str], list[page_models.Page], None] = None
    file_url: Optional[str] = None
    content_type: Optional[str] = None
    rich_text: Optional[dict] = None
    plain_text: Optional[str] = None
    boolean: Optional[bool] = None
    date: Optional[datetime.date] = None
    date_time: Optional[datetime.datetime] = None


T_INSTANCE = Union[
    product_models.Product, product_models.ProductVariant, page_models.Page
]
T_INPUT_MAP = list[tuple[attribute_models.Attribute, AttrValuesInput]]
T_ERROR_DICT = dict[tuple[str, str], list]

EntityTypeData = namedtuple("EntityTypeData", ["model", "name_field", "value_field"])


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

    # Defines the entity type corresponding model, the model field that should be used
    # to create the value name, and relation field responsible for reference.
    # Should be updated every time, the new `AttributeEntityType` value is added.
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
    }

    @classmethod
    def _resolve_attribute_nodes(
        cls,
        qs: "QuerySet",
        error_class,
        *,
        global_ids: list[str],
        external_references: Iterable[str],
        pks: Iterable[int],
    ):
        """Retrieve attributes nodes from given global IDs or external reference."""

        nodes: list[attribute_models.Attribute] = list(
            qs.filter(
                Q(pk__in=pks) | Q(external_reference__in=external_references)
            ).iterator()
        )

        if not nodes:
            raise ValidationError(
                (
                    f"Could not resolve to a node: ids={global_ids}, "
                    f"external_references={external_references}."
                ),
                code=error_class.NOT_FOUND.value,
            )

        nodes_pk_list = set()
        nodes_external_reference_list = set()

        for node in nodes:
            nodes_pk_list.add(node.pk)
            nodes_external_reference_list.add(node.external_reference)

        for pk, global_id in zip(pks, global_ids):
            if pk not in nodes_pk_list:
                raise ValidationError(
                    f"Could not resolve {global_id!r} to Attribute",
                    code=error_class.NOT_FOUND.value,
                )

        for external_ref in external_references:
            if external_ref not in nodes_external_reference_list:
                raise ValidationError(
                    f"Could not resolve {external_ref} to Attribute",
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
        assignment = instance.attributes.filter(  # type:ignore[union-attr]
            assignment__attribute=attribute, **{f"values__{lookup_field}": value}
        ).first()

        return (
            None
            if assignment is None
            else assignment.values.filter(**{lookup_field: value}).first()
        )

    @classmethod
    def _create_value_instance(cls, attribute, attr_value, external_ref):
        return (
            (
                AttributeValueBulkActionEnum.CREATE,
                AttributeValue(
                    external_reference=external_ref,
                    attribute=attribute,
                    name=attr_value,
                    slug=prepare_unique_attribute_value_slug(
                        attribute, slugify(unidecode(attr_value))
                    ),
                ),
            ),
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
        error_class: Union[type[PageErrorCode], type[ProductErrorCode]] = (
            PageErrorCode if is_page_attributes else ProductErrorCode
        )

        # Mapping to associate the input values back to the resolved attribute nodes
        pks = {}
        external_references_values_map = {}

        # Temporary storage of the passed ID for error reporting
        global_ids = []

        for attribute_input in raw_input:
            global_id = attribute_input.pop("id", None)
            external_reference = attribute_input.pop("external_reference", None)

            try:
                validate_one_of_args_is_in_mutation(
                    "id",
                    global_id,
                    "external_reference",
                    external_reference,
                    use_camel_case=True,
                )
            except ValidationError as error:
                raise ValidationError(
                    error.message,
                    code=error_class.REQUIRED.value,
                )

            values = AttrValuesInput(
                global_id=global_id,
                external_reference=external_reference,
                values=attribute_input.pop("values", []),
                file_url=cls._clean_file_url(
                    attribute_input.pop("file", None), error_class
                ),
                **attribute_input,
            )

            if global_id:
                internal_id = cls._resolve_attribute_global_id(error_class, global_id)
                global_ids.append(global_id)
                pks[internal_id] = values

            if external_reference:
                external_references_values_map[external_reference] = values

        attributes = cls._resolve_attribute_nodes(
            attributes_qs,
            error_class,
            global_ids=global_ids,
            external_references=external_references_values_map.keys(),
            pks=pks.keys(),
        )

        attr_with_invalid_references = []
        cleaned_input = []

        for attribute in attributes:
            key = pks.get(attribute.pk)
            if not key:
                key = external_references_values_map[attribute.external_reference]

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
                code=error_class.INVALID.value,
            )

        cls._validate_attributes_input(
            cleaned_input,
            attributes_qs,
            creation=creation,
            is_page_attributes=is_page_attributes,
        )

        return cleaned_input

    @staticmethod
    def _clean_file_url(file_url: Optional[str], error_class):
        # extract storage path from file URL
        storage_root_url = get_default_storage_root_url()
        if file_url and not file_url.startswith(storage_root_url):
            raise ValidationError(
                "The file_url must be the path to the default storage.",
                code=error_class.INVALID.value,
            )
        return (
            re.sub(storage_root_url, "", file_url) if file_url is not None else file_url
        )

    @classmethod
    def _validate_references(
        cls, error_class, attribute: attribute_models.Attribute, values: AttrValuesInput
    ) -> AttrValuesInput:
        references = values.references
        if not references:
            return values

        if not attribute.entity_type:
            # FIXME: entity type is nullable for whatever reason
            raise ValidationError(
                "Invalid reference type.", code=error_class.INVALID.value
            )
        entity_model = cls.ENTITY_TYPE_MAPPING[attribute.entity_type].model
        try:
            ref_instances = get_nodes(
                references, attribute.entity_type, model=entity_model
            )
            values.references = ref_instances
            return values
        except GraphQLError:
            raise ValidationError(
                "Invalid reference type.", code=error_class.INVALID.value
            )

    @classmethod
    def _validate_attributes_input(
        cls,
        cleaned_input: T_INPUT_MAP,
        attribute_qs: "QuerySet",
        *,
        creation: bool,
        is_page_attributes: bool,
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

        Note: this should always be run inside a transaction.

        :param instance: the product or variant to associate the attribute against.
        :param cleaned_input: the cleaned user input (refer to clean_attributes)
        """
        pre_save_methods_mapping = {
            AttributeInputType.BOOLEAN: cls._pre_save_boolean_values,
            AttributeInputType.DATE: cls._pre_save_date_time_values,
            AttributeInputType.DATE_TIME: cls._pre_save_date_time_values,
            AttributeInputType.DROPDOWN: cls._pre_save_dropdown_value,
            AttributeInputType.SWATCH: cls._pre_save_swatch_value,
            AttributeInputType.FILE: cls._pre_save_file_value,
            AttributeInputType.NUMERIC: cls._pre_save_numeric_values,
            AttributeInputType.MULTISELECT: cls._pre_save_multiselect_values,
            AttributeInputType.PLAIN_TEXT: cls._pre_save_plain_text_values,
            AttributeInputType.REFERENCE: cls._pre_save_reference_values,
            AttributeInputType.RICH_TEXT: cls._pre_save_rich_text_values,
        }
        clean_assignment = []
        pre_save_bulk = defaultdict(
            lambda: defaultdict(list)  # type: ignore[var-annotated]
        )
        attr_val_map = defaultdict(list)

        for attribute, attr_values in cleaned_input:
            is_handled_by_values_field = (
                attr_values.values
                and attribute.input_type
                in (
                    AttributeInputType.DROPDOWN,
                    AttributeInputType.MULTISELECT,
                    AttributeInputType.SWATCH,
                )
            )
            if is_handled_by_values_field:
                attribute_values = cls._pre_save_values(attribute, attr_values)
            else:
                pre_save_func = pre_save_methods_mapping[attribute.input_type]
                attribute_values = pre_save_func(instance, attribute, attr_values)

            if not attribute_values:
                # to ensure that attribute will be present in variable `pre_save_bulk`,
                # so function `associate_attribute_values_to_instance` will be called
                # properly for all attributes, even in case when attribute has no values
                pre_save_bulk[AttributeValueBulkActionEnum.NONE].setdefault(
                    attribute, []
                )
            else:
                for key, value in attribute_values:
                    pre_save_bulk[key][attribute].append(value)

        attribute_and_values = cls._bulk_create_pre_save_values(pre_save_bulk)

        for attribute, values in attribute_and_values.items():
            if not values:
                clean_assignment.append(attribute.pk)
            else:
                attr_val_map[attribute.pk].extend(values)

        associate_attribute_values_to_instance(instance, attr_val_map)

        # drop attribute assignment model when values are unassigned from instance
        if clean_assignment:
            instance.attributes.filter(  # type:ignore[union-attr]
                assignment__attribute_id__in=clean_assignment
            ).delete()

    @classmethod
    def _pre_save_dropdown_value(
        cls,
        _,
        attribute: attribute_models.Attribute,
        attr_values: AttrValuesInput,
    ):
        if not attr_values.dropdown:
            return tuple()

        attr_value = attr_values.dropdown.value
        external_ref = attr_values.dropdown.external_reference

        if external_ref and attr_value:
            return cls._create_value_instance(attribute, attr_value, external_ref)

        if external_ref:
            value = attribute_models.AttributeValue.objects.get(
                external_reference=external_ref
            )
            if not value:
                raise ValidationError(
                    "Attribute value with given externalReference can't be found"
                )
            return ((AttributeValueBulkActionEnum.NONE, value),)

        if id := attr_values.dropdown.id:
            _, attr_value_id = from_global_id_or_error(id)
            value = attribute_models.AttributeValue.objects.get(pk=attr_value_id)
            if not value:
                raise ValidationError("Attribute value with given ID can't be found")
            return ((AttributeValueBulkActionEnum.NONE, value),)

        if attr_value:
            return cls._prepare_attribute_values(attribute, [attr_value])

        return tuple()

    @classmethod
    def _pre_save_swatch_value(
        cls,
        _,
        attribute: attribute_models.Attribute,
        attr_values: AttrValuesInput,
    ):
        if not attr_values.swatch:
            return tuple()

        attr_value = attr_values.swatch.value
        external_ref = attr_values.swatch.external_reference

        if external_ref and attr_value:
            value = cls._create_value_instance(attribute, attr_value, external_ref)
            return value

        if external_ref:
            value = attribute_models.AttributeValue.objects.filter(
                external_reference=external_ref
            ).first()
            if not value:
                raise ValidationError(
                    "Attribute value with given externalReference can't be found"
                )
            return (
                (
                    AttributeValueBulkActionEnum.NONE,
                    value,
                ),
            )

        if id := attr_values.swatch.id:
            _, attr_value_id = from_global_id_or_error(id)
            value = attribute_models.AttributeValue.objects.filter(
                pk=attr_value_id
            ).first()
            if not value:
                raise ValidationError("Attribute value with given ID can't be found")
            return (
                (
                    AttributeValueBulkActionEnum.NONE,
                    value,
                ),
            )

        if attr_value := attr_values.swatch.value:
            return cls._prepare_attribute_values(attribute, [attr_value])

        return tuple()

    @classmethod
    def _pre_save_multiselect_values(
        cls,
        _,
        attribute: attribute_models.Attribute,
        attr_values_input: AttrValuesInput,
    ):
        if not attr_values_input.multiselect:
            return tuple()

        attribute_values: list[attribute_models.AttributeValue] = []
        for attr_value in attr_values_input.multiselect:
            external_ref = attr_value.external_reference

            if external_ref and attr_value.value:
                return cls._create_value_instance(
                    attribute, attr_value.value, external_ref
                )

            if external_ref:
                value = attribute_models.AttributeValue.objects.get(
                    external_reference=external_ref
                )
                if not value:
                    raise ValidationError(
                        "Attribute value with given externalReference can't be found"
                    )
                attribute_values.append(value)

            if attr_value.id:
                _, attr_value_id = from_global_id_or_error(attr_value.id)
                attr_value_model = attribute_models.AttributeValue.objects.get(
                    pk=attr_value_id
                )
                if not attr_value_model:
                    raise ValidationError(
                        "Attribute value with given ID can't be found"
                    )
                if attr_value_model.id not in [a.id for a in attribute_values]:
                    attribute_values.append(attr_value_model)

            if attr_value.value:
                attr_value_model = prepare_attribute_values(
                    attribute, [attr_value.value]
                )[0][0]
                attr_value_model.save()
                if attr_value_model.id not in [a.id for a in attribute_values]:
                    attribute_values.append(attr_value_model)

        return [
            (AttributeValueBulkActionEnum.NONE, value) for value in attribute_values
        ]

    @classmethod
    def _pre_save_numeric_values(
        cls,
        instance: T_INSTANCE,
        attribute: attribute_models.Attribute,
        attr_values: AttrValuesInput,
    ):
        if attr_values.values:
            value = attr_values.values[0]
        elif attr_values.numeric:
            value = attr_values.numeric
        else:
            return tuple()

        defaults = {
            "name": value,
        }
        return cls._update_or_create_value(instance, attribute, defaults)

    @classmethod
    def _pre_save_values(
        cls, attribute: attribute_models.Attribute, attr_values: AttrValuesInput
    ):
        """To be deprecated together with `AttributeValueInput.values` field.

        Lazy-retrieve or create the database objects from the supplied raw values.
        """

        if not attr_values.values:
            return tuple()

        return cls._prepare_attribute_values(attribute, attr_values.values)

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
        _instance: T_INSTANCE,
        attribute: attribute_models.Attribute,
        attr_values: AttrValuesInput,
    ):
        if attr_values.boolean is None:
            return tuple()

        boolean = bool(attr_values.boolean)
        value = {
            "attribute": attribute,
            "slug": slugify(unidecode(f"{attribute.id}_{boolean}")),
            "defaults": {
                "name": f"{attribute.name}: {'Yes' if boolean else 'No'}",
                "boolean": boolean,
            },
        }
        return ((AttributeValueBulkActionEnum.GET_OR_CREATE, value),)

    @classmethod
    def _pre_save_date_time_values(
        cls,
        instance: T_INSTANCE,
        attribute: attribute_models.Attribute,
        attr_values: AttrValuesInput,
    ):
        is_date_attr = attribute.input_type == AttributeInputType.DATE
        tz = timezone.utc
        if is_date_attr:
            if not attr_values.date:
                return ()
            value = str(attr_values.date)
            date_time = datetime.datetime(
                attr_values.date.year,
                attr_values.date.month,
                attr_values.date.day,
                0,
                0,
                tzinfo=tz,
            )
        else:
            if not attr_values.date_time:
                return ()
            value = str(attr_values.date_time)
            date_time = attr_values.date_time
        defaults = {"name": value, "date_time": date_time}
        return cls._update_or_create_value(instance, attribute, defaults)

    @classmethod
    def _update_or_create_value(
        cls,
        instance: T_INSTANCE,
        attribute: attribute_models.Attribute,
        value_defaults: dict,
    ):
        slug = slugify(unidecode(f"{instance.id}_{attribute.id}"))
        value = {
            "attribute": attribute,
            "slug": slug,
            "defaults": value_defaults,
        }
        return ((AttributeValueBulkActionEnum.UPDATE_OR_CREATE, value),)

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
        if not attr_values.references or not attribute.entity_type:
            return tuple()

        entity_data = cls.ENTITY_TYPE_MAPPING[attribute.entity_type]
        field_name = entity_data.name_field

        reference_list = []
        attr_value_field = entity_data.value_field
        for ref in attr_values.references:
            name = getattr(ref, field_name)
            if attribute.entity_type == AttributeEntityType.PRODUCT_VARIANT:
                name = f"{ref.product.name}: {name}"  # type: ignore

            reference_list.append(
                (
                    AttributeValueBulkActionEnum.GET_OR_CREATE,
                    {
                        "attribute": attribute,
                        "slug": slugify(
                            unidecode(f"{instance.id}_{ref.id}")  # type: ignore
                        ),
                        "defaults": {"name": name},
                        attr_value_field: ref,
                    },
                )
            )

        return reference_list

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
            value = AttributeValue(
                attribute=attribute,
                file_url=file_url,
                name=name,
                content_type=attr_value.content_type,
            )
            value.slug = generate_unique_slug(value, name)
            return ((AttributeValueBulkActionEnum.CREATE, value),)
        return ((None, value),)

    @classmethod
    def _prepare_attribute_values(cls, attribute, values):
        results, values_to_create = prepare_attribute_values(attribute, values)
        return [
            (AttributeValueBulkActionEnum.NONE, record)
            for record in results
            if record not in values_to_create
        ] + [
            (AttributeValueBulkActionEnum.CREATE, record) for record in values_to_create
        ]

    @classmethod
    def _bulk_create_pre_save_values(cls, pre_save_bulk):
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


class PageAttributeAssignmentMixin(AttributeAssignmentMixin):
    # TODO: Merge the code here with the mixin above
    # after the refactor of Page <> Attribute and
    # Product <> Attribute dedicated mixins
    # should me merged into AttributeAssignmentMixin

    @classmethod
    def _get_assigned_attribute_value_if_exists(
        cls,
        instance: T_INSTANCE,
        attribute: attribute_models.Attribute,
        lookup_field: str,
        value,
    ):
        assigned_values = attribute_models.AssignedPageAttributeValue.objects.filter(
            page_id=instance.pk
        )

        return attribute_models.AttributeValue.objects.filter(
            Exists(assigned_values.filter(value_id=OuterRef("id"))),
            attribute_id=attribute.pk,
            **{lookup_field: value},
        ).first()

    @classmethod
    def save(
        cls,
        instance: T_INSTANCE,
        cleaned_input: T_INPUT_MAP,
    ):
        """Save the cleaned input into the database against the given instance.

        Note: this should always be ran inside a transaction.
        :param instance: the product or variant to associate the attribute against.
        :param cleaned_input: the cleaned user input (refer to clean_attributes)
        """
        pre_save_methods_mapping = {
            AttributeInputType.BOOLEAN: cls._pre_save_boolean_values,
            AttributeInputType.DATE: cls._pre_save_date_time_values,
            AttributeInputType.DATE_TIME: cls._pre_save_date_time_values,
            AttributeInputType.DROPDOWN: cls._pre_save_dropdown_value,
            AttributeInputType.SWATCH: cls._pre_save_swatch_value,
            AttributeInputType.FILE: cls._pre_save_file_value,
            AttributeInputType.NUMERIC: cls._pre_save_numeric_values,
            AttributeInputType.MULTISELECT: cls._pre_save_multiselect_values,
            AttributeInputType.PLAIN_TEXT: cls._pre_save_plain_text_values,
            AttributeInputType.REFERENCE: cls._pre_save_reference_values,
            AttributeInputType.RICH_TEXT: cls._pre_save_rich_text_values,
        }

        clean_assignment = []
        pre_save_bulk = defaultdict(
            lambda: defaultdict(list)  # type: ignore[var-annotated]
        )
        attr_val_map = defaultdict(list)

        for attribute, attr_values in cleaned_input:
            is_handled_by_values_field = (
                attr_values.values
                and attribute.input_type
                in (
                    AttributeInputType.DROPDOWN,
                    AttributeInputType.MULTISELECT,
                    AttributeInputType.SWATCH,
                )
            )
            if is_handled_by_values_field:
                attribute_values = cls._pre_save_values(attribute, attr_values)
            else:
                pre_save_func = pre_save_methods_mapping[attribute.input_type]
                attribute_values = pre_save_func(instance, attribute, attr_values)

            if not attribute_values:
                # to ensure that attribute will be present in variable `pre_save_bulk`,
                # so function `associate_attribute_values_to_instance` will be called
                # properly for all attributes, even in case when attribute has no values
                pre_save_bulk[AttributeValueBulkActionEnum.NONE].setdefault(
                    attribute, []
                )
            else:
                for key, value in attribute_values:
                    pre_save_bulk[key][attribute].append(value)

        attribute_and_values = cls._bulk_create_pre_save_values(pre_save_bulk)

        for attribute, values in attribute_and_values.items():
            if not values:
                clean_assignment.append(attribute.pk)
            else:
                attr_val_map[attribute.pk].extend(values)

        associate_attribute_values_to_instance(instance, attr_val_map)

        if clean_assignment:
            values = attribute_models.AttributeValue.objects.filter(
                attribute_id__in=clean_assignment
            )
            attribute_models.AssignedPageAttributeValue.objects.filter(
                Exists(values.filter(id=OuterRef("value_id"))),
                page_id=instance.pk,
            ).delete()


class ProductAttributeAssignmentMixin(AttributeAssignmentMixin):
    # TODO: merge the code here with the mixin above
    # when all attribute relations are cleaned up

    @classmethod
    def _get_assigned_attribute_value_if_exists(
        cls,
        instance: T_INSTANCE,
        attribute: attribute_models.Attribute,
        lookup_field: str,
        value,
    ):
        assigned_values = attribute_models.AssignedProductAttributeValue.objects.filter(
            product_id=instance.pk
        )

        return attribute_models.AttributeValue.objects.filter(
            Exists(assigned_values.filter(value_id=OuterRef("id"))),
            attribute_id=attribute.pk,
            **{lookup_field: value},
        ).first()

    @classmethod
    def save(
        cls,
        instance: T_INSTANCE,
        cleaned_input: T_INPUT_MAP,
    ):
        """Save the cleaned input into the database against the given instance.

        Note: this should always be ran inside a transaction.

        :param instance: the product or variant to associate the attribute against.
        :param cleaned_input: the cleaned user input (refer to clean_attributes)
        """
        pre_save_methods_mapping = {
            AttributeInputType.BOOLEAN: cls._pre_save_boolean_values,
            AttributeInputType.DATE: cls._pre_save_date_time_values,
            AttributeInputType.DATE_TIME: cls._pre_save_date_time_values,
            AttributeInputType.DROPDOWN: cls._pre_save_dropdown_value,
            AttributeInputType.SWATCH: cls._pre_save_swatch_value,
            AttributeInputType.FILE: cls._pre_save_file_value,
            AttributeInputType.NUMERIC: cls._pre_save_numeric_values,
            AttributeInputType.MULTISELECT: cls._pre_save_multiselect_values,
            AttributeInputType.PLAIN_TEXT: cls._pre_save_plain_text_values,
            AttributeInputType.REFERENCE: cls._pre_save_reference_values,
            AttributeInputType.RICH_TEXT: cls._pre_save_rich_text_values,
        }

        clean_assignment = []
        pre_save_bulk = defaultdict(
            lambda: defaultdict(list)  # type: ignore[var-annotated]
        )
        attr_val_map = defaultdict(list)
        for attribute, attr_values in cleaned_input:
            is_handled_by_values_field = (
                attr_values.values
                and attribute.input_type
                in (
                    AttributeInputType.DROPDOWN,
                    AttributeInputType.MULTISELECT,
                    AttributeInputType.SWATCH,
                )
            )
            if is_handled_by_values_field:
                attribute_values = cls._pre_save_values(attribute, attr_values)
            else:
                pre_save_func = pre_save_methods_mapping[attribute.input_type]
                attribute_values = pre_save_func(instance, attribute, attr_values)

            if not attribute_values:
                # to ensure that attribute will be present in variable `pre_save_bulk`,
                # so function `associate_attribute_values_to_instance` will be called
                # properly for all attributes, even in case when attribute has no values
                pre_save_bulk[AttributeValueBulkActionEnum.NONE].setdefault(
                    attribute, []
                )
            else:
                for key, value in attribute_values:
                    pre_save_bulk[key][attribute].append(value)

        attribute_and_values = cls._bulk_create_pre_save_values(pre_save_bulk)

        for attribute, values in attribute_and_values.items():
            if not values:
                clean_assignment.append(attribute.pk)
            else:
                attr_val_map[attribute.pk].extend(values)

        associate_attribute_values_to_instance(instance, attr_val_map)

        if clean_assignment:
            values = attribute_models.AttributeValue.objects.filter(
                attribute_id__in=clean_assignment
            )
            attribute_models.AssignedProductAttributeValue.objects.filter(
                Exists(values.filter(id=OuterRef("value_id"))),
                product_id=instance.pk,
            ).delete()


def prepare_attribute_values(attribute: attribute_models.Attribute, values: list[str]):
    slug_to_value_map = {}
    name_to_value_map = {}
    for val in attribute.values.filter(Q(name__in=values) | Q(slug__in=values)):
        slug_to_value_map[val.slug] = val
        name_to_value_map[val.name] = val

    existing_slugs = get_existing_slugs(attribute, values)

    result = []
    values_to_create = []
    for value in values:
        # match the value firstly by slug then by name
        value_obj = slug_to_value_map.get(value) or name_to_value_map.get(value)
        if value_obj:
            result.append(value_obj)
        else:
            slug = prepare_unique_slug(slugify(unidecode(value)), existing_slugs)
            instance = attribute_models.AttributeValue(
                attribute=attribute, name=value, slug=slug
            )
            result.append(instance)

            values_to_create.append(instance)

            # the set of existing slugs must be updated to not generate accidentally
            # the same slug for two or more values
            existing_slugs.add(slug)

            # extend name to slug value to not create two elements with the same name
            name_to_value_map[instance.name] = instance

    return result, values_to_create


def get_existing_slugs(attribute: attribute_models.Attribute, values: list[str]):
    lookup = Q()
    for value in values:
        lookup |= Q(slug__startswith=slugify(unidecode(value)))

    existing_slugs = set(attribute.values.filter(lookup).values_list("slug", flat=True))
    return existing_slugs


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
    ERROR_DUPLICATED_VALUES = (
        "Duplicated attribute values are provided.",
        "DUPLICATED_INPUT_ITEM",
    )
    ERROR_ID_AND_VALUE = (
        "Attribute values cannot be assigned by both id and value.",
        "INVALID",
    )
    ERROR_ID_AND_EXTERNAL_REFERENCE = (
        "Attribute values cannot be assigned by both id and external reference.",
        "INVALID",
    )
    ERROR_NO_ID_OR_EXTERNAL_REFERENCE = (
        "Attribute id or external reference has to be provided.",
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
    input_data: list[tuple["Attribute", "AttrValuesInput"]],
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
    input_type_to_validation_func_mapping = {
        AttributeInputType.BOOLEAN: validate_boolean_input,
        AttributeInputType.DATE: validate_date_time_input,
        AttributeInputType.DATE_TIME: validate_date_time_input,
        AttributeInputType.DROPDOWN: validate_dropdown_input,
        AttributeInputType.SWATCH: validate_swatch_input,
        AttributeInputType.FILE: validate_file_attributes_input,
        AttributeInputType.NUMERIC: validate_numeric_input,
        AttributeInputType.MULTISELECT: validate_multiselect_input,
        AttributeInputType.PLAIN_TEXT: validate_plain_text_attributes_input,
        AttributeInputType.REFERENCE: validate_reference_attributes_input,
        AttributeInputType.RICH_TEXT: validate_rich_text_attributes_input,
    }

    for attribute, attr_values in input_data:
        attrs = (
            attribute,
            attr_values,
            attribute_errors,
        )
        is_handled_by_values_field = attr_values.values and attribute.input_type in (
            AttributeInputType.DROPDOWN,
            AttributeInputType.MULTISELECT,
            AttributeInputType.NUMERIC,
            AttributeInputType.SWATCH,
        )
        if is_handled_by_values_field:
            validate_standard_attributes_input(*attrs)
        else:
            validation_func = input_type_to_validation_func_mapping[
                attribute.input_type
            ]
            validation_func(*attrs)

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
    attr_identifier = attr_values.global_id or attr_values.external_reference
    if not attr_identifier:
        attribute_errors[AttributeInputErrors.ERROR_NO_ID_OR_EXTERNAL_REFERENCE].append(
            attr_identifier
        )
        return

    value = attr_values.file_url
    if not value:
        if attribute.value_required:
            attribute_errors[AttributeInputErrors.ERROR_NO_FILE_GIVEN].append(
                attr_identifier
            )
    elif not value.strip():
        attribute_errors[AttributeInputErrors.ERROR_BLANK_FILE_VALUE].append(
            attr_identifier
        )


def validate_reference_attributes_input(
    attribute: "Attribute",
    attr_values: "AttrValuesInput",
    attribute_errors: T_ERROR_DICT,
):
    attr_identifier = attr_values.global_id or attr_values.external_reference
    if not attr_identifier:
        attribute_errors[AttributeInputErrors.ERROR_NO_ID_OR_EXTERNAL_REFERENCE].append(
            attr_identifier
        )
        return

    references = attr_values.references
    if not references:
        if attribute.value_required:
            attribute_errors[AttributeInputErrors.ERROR_NO_REFERENCE_GIVEN].append(
                attr_identifier
            )


def validate_boolean_input(
    attribute: "Attribute",
    attr_values: "AttrValuesInput",
    attribute_errors: T_ERROR_DICT,
):
    attr_identifier = attr_values.global_id or attr_values.external_reference
    if not attr_identifier:
        attribute_errors[AttributeInputErrors.ERROR_NO_ID_OR_EXTERNAL_REFERENCE].append(
            attr_identifier
        )
        return

    value = attr_values.boolean

    if attribute.value_required and value is None:
        attribute_errors[AttributeInputErrors.ERROR_BLANK_VALUE].append(attr_identifier)


def validate_rich_text_attributes_input(
    attribute: "Attribute",
    attr_values: "AttrValuesInput",
    attribute_errors: T_ERROR_DICT,
):
    attr_identifier = attr_values.global_id or attr_values.external_reference
    if not attr_identifier:
        attribute_errors[AttributeInputErrors.ERROR_NO_ID_OR_EXTERNAL_REFERENCE].append(
            attr_identifier
        )
        return

    text = clean_editor_js(attr_values.rich_text or {}, to_string=True)

    if not text.strip() and attribute.value_required:
        attribute_errors[AttributeInputErrors.ERROR_NO_VALUE_GIVEN].append(
            attr_identifier
        )


def validate_plain_text_attributes_input(
    attribute: "Attribute",
    attr_values: "AttrValuesInput",
    attribute_errors: T_ERROR_DICT,
):
    attr_identifier = attr_values.global_id or attr_values.external_reference

    if not attr_identifier:
        attribute_errors[AttributeInputErrors.ERROR_NO_ID_OR_EXTERNAL_REFERENCE].append(
            attr_identifier
        )
        return

    if (
        not attr_values.plain_text or not attr_values.plain_text.strip()
    ) and attribute.value_required:
        attribute_errors[AttributeInputErrors.ERROR_NO_VALUE_GIVEN].append(
            attr_identifier
        )


def validate_standard_attributes_input(
    attribute: "Attribute",
    attr_values: "AttrValuesInput",
    attribute_errors: T_ERROR_DICT,
):
    """To be deprecated together with `AttributeValueInput.values` field."""
    attr_identifier = attr_values.global_id or attr_values.external_reference

    if not attr_identifier:
        attribute_errors[AttributeInputErrors.ERROR_NO_ID_OR_EXTERNAL_REFERENCE].append(
            attr_identifier
        )
        return

    if not attr_values.values:
        if attribute.value_required:
            attribute_errors[AttributeInputErrors.ERROR_NO_VALUE_GIVEN].append(
                attr_identifier
            )
    elif (
        attribute.input_type != AttributeInputType.MULTISELECT
        and len(attr_values.values) != 1
    ):
        attribute_errors[AttributeInputErrors.ERROR_MORE_THAN_ONE_VALUE_GIVEN].append(
            attr_identifier
        )

    if attr_values.values is not None:
        validate_values(
            attr_identifier,
            attribute,
            attr_values.values,
            attribute_errors,
        )


def validate_single_selectable_field(
    attribute: "Attribute",
    attr_value: AttrValuesForSelectableFieldInput,
    attribute_errors: T_ERROR_DICT,
    attr_identifier: str,
):
    id = attr_value.id
    value = attr_value.value
    external_reference = attr_value.external_reference

    if id and external_reference:
        attribute_errors[AttributeInputErrors.ERROR_ID_AND_EXTERNAL_REFERENCE].append(
            attr_identifier
        )
        return

    if id and value:
        attribute_errors[AttributeInputErrors.ERROR_ID_AND_VALUE].append(
            attr_identifier
        )
        return

    if not id and not external_reference and not value and attribute.value_required:
        attribute_errors[AttributeInputErrors.ERROR_NO_VALUE_GIVEN].append(
            attr_identifier
        )
        return

    if value:
        max_length = attribute.values.model.name.field.max_length
        if not value.strip():
            attribute_errors[AttributeInputErrors.ERROR_BLANK_VALUE].append(
                attr_identifier
            )
        elif max_length and len(value) > max_length:
            attribute_errors[AttributeInputErrors.ERROR_MAX_LENGTH].append(
                attr_identifier
            )

    value_identifier = id or external_reference
    if value_identifier:
        if not value_identifier.strip():
            attribute_errors[AttributeInputErrors.ERROR_BLANK_VALUE].append(
                attr_identifier
            )


def validate_dropdown_input(
    attribute: "Attribute",
    attr_values: "AttrValuesInput",
    attribute_errors: T_ERROR_DICT,
):
    attr_identifier = attr_values.global_id or attr_values.external_reference
    if not attr_identifier:
        attribute_errors[AttributeInputErrors.ERROR_NO_ID_OR_EXTERNAL_REFERENCE].append(
            attr_identifier
        )
        return

    if not attr_values.dropdown:
        if attribute.value_required:
            attribute_errors[AttributeInputErrors.ERROR_NO_VALUE_GIVEN].append(
                attr_identifier
            )
    else:
        validate_single_selectable_field(
            attribute,
            attr_values.dropdown,
            attribute_errors,
            attr_identifier,
        )


def validate_swatch_input(
    attribute: "Attribute",
    attr_values: "AttrValuesInput",
    attribute_errors: T_ERROR_DICT,
):
    attr_identifier = attr_values.global_id or attr_values.external_reference
    if not attr_identifier:
        attribute_errors[AttributeInputErrors.ERROR_NO_ID_OR_EXTERNAL_REFERENCE].append(
            attr_identifier
        )
        return

    if not attr_values.swatch:
        if attribute.value_required:
            attribute_errors[AttributeInputErrors.ERROR_NO_VALUE_GIVEN].append(
                attr_identifier
            )
    else:
        validate_single_selectable_field(
            attribute,
            attr_values.swatch,
            attribute_errors,
            attr_identifier,
        )


def validate_multiselect_input(
    attribute: "Attribute",
    attr_values: "AttrValuesInput",
    attribute_errors: T_ERROR_DICT,
):
    attr_identifier = attr_values.global_id or attr_values.external_reference
    if not attr_identifier:
        attribute_errors[AttributeInputErrors.ERROR_NO_ID_OR_EXTERNAL_REFERENCE].append(
            attr_identifier
        )
        return

    multi_values = attr_values.multiselect
    if not multi_values:
        if attribute.value_required:
            attribute_errors[AttributeInputErrors.ERROR_NO_VALUE_GIVEN].append(
                attr_identifier
            )
    else:
        ids = [value.id for value in multi_values if value.id is not None]
        values = [value.value for value in multi_values if value.value is not None]
        external_refs = [
            value.external_reference
            for value in multi_values
            if value.external_reference is not None
        ]
        if ids and values:
            attribute_errors[AttributeInputErrors.ERROR_ID_AND_VALUE].append(
                attr_identifier
            )
            return
        if not ids and not external_refs and not values and attribute.value_required:
            attribute_errors[AttributeInputErrors.ERROR_NO_VALUE_GIVEN].append(
                attr_identifier
            )
            return

        if (
            len(ids) > len(set(ids))
            or len(values) > len(set(values))
            or len(external_refs) > len(set(external_refs))
        ):
            attribute_errors[AttributeInputErrors.ERROR_DUPLICATED_VALUES].append(
                attr_identifier
            )
            return

        for attr_value in multi_values:
            validate_single_selectable_field(
                attribute,
                attr_value,
                attribute_errors,
                attr_identifier,
            )


def validate_numeric_input(
    attribute: "Attribute",
    attr_values: "AttrValuesInput",
    attribute_errors: T_ERROR_DICT,
):
    attribute_id = attr_values.global_id
    if attr_values.numeric is None:
        if attribute.value_required:
            attribute_errors[AttributeInputErrors.ERROR_NO_VALUE_GIVEN].append(
                attribute_id
            )
            return
        return

    try:
        float(attr_values.numeric)
    except ValueError:
        attribute_errors[AttributeInputErrors.ERROR_NUMERIC_VALUE_REQUIRED].append(
            attribute_id
        )

    if isinstance(attr_values.numeric, bool):
        attribute_errors[AttributeInputErrors.ERROR_NUMERIC_VALUE_REQUIRED].append(
            attribute_id
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
    attr_identifier: str,
    attribute: "Attribute",
    values: list,
    attribute_errors: T_ERROR_DICT,
):
    """To be deprecated together with `AttributeValueInput.values` field."""
    name_field = attribute.values.model.name.field
    is_numeric = attribute.input_type == AttributeInputType.NUMERIC
    if get_duplicated_values(values):
        attribute_errors[AttributeInputErrors.ERROR_DUPLICATED_VALUES].append(
            attr_identifier
        )
    for value in values:
        if value is None or (not is_numeric and not value.strip()):
            attribute_errors[AttributeInputErrors.ERROR_BLANK_VALUE].append(
                attr_identifier
            )
        elif is_numeric:
            try:
                float(value)
            except ValueError:
                attribute_errors[
                    AttributeInputErrors.ERROR_NUMERIC_VALUE_REQUIRED
                ].append(attr_identifier)
        elif name_field.max_length and len(value) > name_field.max_length:
            attribute_errors[AttributeInputErrors.ERROR_MAX_LENGTH].append(
                attr_identifier
            )


def validate_required_attributes(
    input_data: list[tuple["Attribute", "AttrValuesInput"]],
    attribute_qs: "QuerySet",
    errors: list[ValidationError],
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
            code=error_code_enum.REQUIRED.value,
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

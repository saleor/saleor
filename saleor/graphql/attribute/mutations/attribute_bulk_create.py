from collections import defaultdict
from typing import Union

import graphene
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from graphene.utils.str_converters import to_camel_case
from text_unidecode import unidecode

from ....attribute import ATTRIBUTE_PROPERTIES_CONFIGURATION, AttributeInputType, models
from ....attribute.error_codes import AttributeBulkCreateErrorCode
from ....core.tracing import traced_atomic_transaction
from ....core.utils import prepare_unique_slug
from ....permission.enums import PageTypePermissions, ProductTypePermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_315, PREVIEW_FEATURE
from ...core.doc_category import DOC_CATEGORY_ATTRIBUTES
from ...core.enums import ErrorPolicyEnum
from ...core.mutations import BaseMutation, ModelMutation
from ...core.types import AttributeBulkCreateError, BaseObjectType, NonNullList
from ...core.utils import WebhookEventInfo, get_duplicated_values
from ...plugins.dataloaders import get_plugin_manager_promise
from ..enums import AttributeTypeEnum
from ..mutations.attribute_create import AttributeCreateInput, AttributeValueCreateInput
from ..types import Attribute

ONLY_SWATCH_FIELDS = ["file_url", "content_type", "value"]
DEPRECATED_ATTR_FIELDS = [
    "storefront_search_position",
    "filterable_in_storefront",
    "available_in_grid",
]
DEPRECATED_VALUE_FIELDS = ["rich_text", "plain_text"]


def validate_value(
    value_data: AttributeCreateInput,
    input_type: AttributeInputType,
    slugs_list: list[str],
    value_index: int,
    attribute_index: int,
    index_error_map: dict[int, list],
    path_prefix="values",
    error_class=AttributeBulkCreateError,
):
    name = value_data.get("name")
    is_swatch_attr = input_type == AttributeInputType.SWATCH

    if is_swatch_attr and value_data.get("value") and value_data.get("file_url"):
        index_error_map[attribute_index].append(
            error_class(
                path=f"{path_prefix}.{value_index}",
                message=("Cannot specify both value and file for swatch attribute."),
                code=error_class.code.INVALID.value,
            )
        )

    if not is_swatch_attr and any(
        [value_data.get(field) for field in ONLY_SWATCH_FIELDS]
    ):
        message = (
            "Cannot define value, file and contentType fields for not "
            "swatch attribute."
        )
        index_error_map[attribute_index].append(
            error_class(
                path=f"{path_prefix}.{value_index}",
                message=message,
                code=error_class.code.INVALID.value,
            )
        )

    slug_value = prepare_unique_slug(slugify(unidecode(name)), slugs_list)
    value_data["slug"] = slug_value
    slugs_list.append(slug_value)

    return value_data


def clean_values(
    values: list,
    input_type: AttributeInputType,
    values_existing_external_refs: set,
    duplicated_values_external_ref: set,
    attribute_index: int,
    index_error_map: dict[int, list],
    attribute=None,
    path_prefix="values",
    error_class=AttributeBulkCreateError,
):
    cleand_values: list = []
    slugs_list: list = []

    if attribute:
        slugs_list = list(attribute.values.values_list("slug", flat=True))

    duplicated_names = get_duplicated_values(
        [
            unidecode(value_data.name.lower().strip())
            for value_data in values
            if value_data.name
        ]
    )

    for value_index, value_data in enumerate(values):
        external_ref = value_data.external_reference
        if external_ref in duplicated_values_external_ref:
            index_error_map[attribute_index].append(
                error_class(
                    path=f"{path_prefix}.{value_index}.externalReference",
                    message="Duplicated external reference.",
                    code=error_class.code.DUPLICATED_INPUT_ITEM.value,
                )
            )
            continue

        if external_ref and external_ref in values_existing_external_refs:
            index_error_map[attribute_index].append(
                error_class(
                    path=f"{path_prefix}.{value_index}.externalReference",
                    message="External reference already exists.",
                    code=error_class.code.UNIQUE.value,
                )
            )
            continue

        if not value_data.name:
            index_error_map[attribute_index].append(
                error_class(
                    path=f"{path_prefix}.{value_index}.name",
                    message="The field is required.",
                    code=error_class.code.REQUIRED.value,
                )
            )
            continue

        if unidecode(value_data.name.lower().strip()) in duplicated_names:
            index_error_map[attribute_index].append(
                error_class(
                    path=f"{path_prefix}.{value_index}.name",
                    message="Duplicated name.",
                    code=error_class.code.DUPLICATED_INPUT_ITEM.value,
                )
            )
            continue

        if value_data.value and input_type not in AttributeInputType.TYPES_WITH_CHOICES:
            index_error_map[attribute_index].append(
                error_class(
                    path="values",
                    message=(f"Values cannot be used with input type {input_type}.",),
                    code=error_class.code.INVALID.value,
                )
            )
            continue

        if any(key in DEPRECATED_VALUE_FIELDS for key in value_data.keys()):
            message = (
                "Deprecated fields 'rich_text', 'plain_text' and are not "
                "allowed in bulk mutation."
            )
            index_error_map[attribute_index].append(
                AttributeBulkCreateError(
                    path=f"{path_prefix}.{value_index}",
                    message=message,
                    code=error_class.code.INVALID.value,
                )
            )
            continue

        validate_value(
            value_data,
            input_type,
            slugs_list,
            value_index,
            attribute_index,
            index_error_map,
            path_prefix,
            error_class,
        )
        cleand_values.append(value_data)

    return cleand_values


class AttributeBulkCreateResult(BaseObjectType):
    attribute = graphene.Field(Attribute, description="Attribute data.")
    errors = NonNullList(
        AttributeBulkCreateError,
        required=False,
        description="List of errors occurred on create attempt.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES


def get_results(
    instances_data_with_errors_list: list[dict], reject_everything: bool = False
) -> list[AttributeBulkCreateResult]:
    return [
        AttributeBulkCreateResult(
            attribute=None if reject_everything else data.get("instance"),
            errors=data.get("errors"),
        )
        for data in instances_data_with_errors_list
    ]


class AttributeBulkCreate(BaseMutation):
    count = graphene.Int(
        required=True,
        description="Returns how many objects were created.",
    )
    results = NonNullList(
        AttributeBulkCreateResult,
        required=True,
        default_value=[],
        description="List of the created attributes.",
    )

    class Arguments:
        attributes = NonNullList(
            AttributeCreateInput,
            required=True,
            description="Input list of attributes to create.",
        )
        error_policy = ErrorPolicyEnum(
            required=False,
            description="Policies of error handling. DEFAULT: "
            + ErrorPolicyEnum.REJECT_EVERYTHING.name,
        )

    class Meta:
        description = "Creates attributes." + ADDED_IN_315 + PREVIEW_FEATURE
        doc_category = DOC_CATEGORY_ATTRIBUTES
        error_type_class = AttributeBulkCreateError
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.ATTRIBUTE_CREATED,
                description="An attribute was created.",
            ),
        ]

    @classmethod
    def clean_attributes(
        cls,
        info: ResolveInfo,
        attributes_data: list[AttributeCreateInput],
        index_error_map: dict[int, list[AttributeBulkCreateError]],
    ):
        cleaned_inputs_map: dict = {}

        attr_input_external_refs = [
            attribute_data.external_reference
            for attribute_data in attributes_data
            if attribute_data.external_reference
        ]
        attrs_existing_external_refs = set(
            models.Attribute.objects.filter(
                external_reference__in=attr_input_external_refs
            ).values_list("external_reference", flat=True)
        )
        duplicated_external_ref = get_duplicated_values(attr_input_external_refs)

        existing_slugs = set(
            models.Attribute.objects.filter(
                slug__in=[
                    slugify(unidecode(attribute_data.name))
                    for attribute_data in attributes_data
                ]
            ).values_list("slug", flat=True)
        )

        values_input_external_refs = [
            value.external_reference
            for attribute_data in attributes_data
            if attribute_data.values
            for value in attribute_data.values
            if value.external_reference
        ]
        values_existing_external_refs = set(
            models.AttributeValue.objects.filter(
                external_reference__in=values_input_external_refs
            ).values_list("external_reference", flat=True)
        )
        duplicated_values_external_ref = get_duplicated_values(
            values_input_external_refs
        )

        for attribute_index, attribute_data in enumerate(attributes_data):
            external_ref = attribute_data.external_reference
            if external_ref in duplicated_external_ref:
                index_error_map[attribute_index].append(
                    AttributeBulkCreateError(
                        path="externalReference",
                        message="Duplicated external reference.",
                        code=AttributeBulkCreateErrorCode.DUPLICATED_INPUT_ITEM.value,
                    )
                )
                cleaned_inputs_map[attribute_index] = None
                continue

            if external_ref and external_ref in attrs_existing_external_refs:
                index_error_map[attribute_index].append(
                    AttributeBulkCreateError(
                        path="externalReference",
                        message="External reference already exists.",
                        code=AttributeBulkCreateErrorCode.UNIQUE.value,
                    )
                )
                cleaned_inputs_map[attribute_index] = None
                continue

            if any(key in DEPRECATED_ATTR_FIELDS for key in attribute_data.keys()):
                message = (
                    "Deprecated fields 'storefront_search_position', "
                    "'filterable_in_storefront', 'available_in_grid' and are not "
                    "allowed in bulk mutation."
                )
                index_error_map[attribute_index].append(
                    AttributeBulkCreateError(
                        message=message,
                        code=AttributeBulkCreateErrorCode.INVALID.value,
                    )
                )
                cleaned_inputs_map[attribute_index] = None
                continue

            cleaned_input = cls.clean_attribute_input(
                info,
                attribute_data,
                attribute_index,
                existing_slugs,
                values_existing_external_refs,
                duplicated_values_external_ref,
                index_error_map,
            )
            cleaned_inputs_map[attribute_index] = cleaned_input
        return cleaned_inputs_map

    @classmethod
    def clean_attribute_input(
        cls,
        info: ResolveInfo,
        attribute_data: AttributeCreateInput,
        attribute_index: int,
        existing_slugs: set,
        values_existing_external_refs: set,
        duplicated_values_external_ref: set,
        index_error_map: dict[int, list[AttributeBulkCreateError]],
    ):
        values = attribute_data.pop("values", None)
        cleaned_input = ModelMutation.clean_input(
            info, None, attribute_data, input_cls=AttributeCreateInput
        )

        # check permissions based on attribute type
        permissions: Union[tuple[ProductTypePermissions], tuple[PageTypePermissions]]
        if cleaned_input["type"] == AttributeTypeEnum.PRODUCT_TYPE.value:
            permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        else:
            permissions = (PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,)

        if not cls.check_permissions(info.context, permissions):
            index_error_map[attribute_index].append(
                AttributeBulkCreateError(
                    message=(
                        "You have no permission to manage this type of attributes. "
                        f"You need one of the following permissions: {permissions}"
                    ),
                    code=AttributeBulkCreateErrorCode.REQUIRED.value,
                )
            )
            return None

        input_type = cleaned_input.get("input_type")
        entity_type = cleaned_input.get("entity_type")
        if input_type == AttributeInputType.REFERENCE and not entity_type:
            index_error_map[attribute_index].append(
                AttributeBulkCreateError(
                    path="entityType",
                    message=(
                        "Entity type is required when REFERENCE input type is used."
                    ),
                    code=AttributeBulkCreateErrorCode.REQUIRED.value,
                )
            )
            return None

        # check attribute configuration
        for field in ATTRIBUTE_PROPERTIES_CONFIGURATION.keys():
            allowed_input_type = ATTRIBUTE_PROPERTIES_CONFIGURATION[field]

            if input_type not in allowed_input_type and cleaned_input.get(field):
                camel_case_field = to_camel_case(field)
                index_error_map[attribute_index].append(
                    AttributeBulkCreateError(
                        path=camel_case_field,
                        message=(
                            f"Cannot set {camel_case_field} on a {input_type} "
                            "attribute.",
                        ),
                        code=AttributeBulkCreateErrorCode.INVALID.value,
                    )
                )
                return None

        # generate slug
        cleaned_input["slug"] = cls._generate_slug(cleaned_input, existing_slugs)

        if values:
            cleaned_values = clean_values(
                values,
                input_type,
                values_existing_external_refs,
                duplicated_values_external_ref,
                attribute_index,
                index_error_map,
            )
            cleaned_input["values"] = cleaned_values

        return cleaned_input

    @classmethod
    def _generate_slug(cls, cleaned_input, existing_slugs):
        name = cleaned_input.get("name")
        slug = slugify(unidecode(name))

        unique_slug = prepare_unique_slug(slug, existing_slugs)
        existing_slugs.add(unique_slug)

        return unique_slug

    @classmethod
    def create_attributes(
        cls,
        info: ResolveInfo,
        cleaned_inputs_map: dict[int, dict],
        error_policy: str,
        index_error_map: dict[int, list[AttributeBulkCreateError]],
    ) -> list[dict]:
        instances_data_and_errors_list: list[dict] = []

        for index, cleaned_input in cleaned_inputs_map.items():
            if not cleaned_input:
                instances_data_and_errors_list.append(
                    {"instance": None, "errors": index_error_map[index]}
                )
                continue

            values: list = []
            values_data = cleaned_input.pop("values", None)
            instance = models.Attribute()

            try:
                instance = cls.construct_instance(instance, cleaned_input)
                cls.clean_instance(info, instance)

                instances_data_and_errors_list.append(
                    {
                        "instance": instance,
                        "errors": index_error_map[index],
                        "values": values,
                    }
                )
            except ValidationError as exc:
                for key, errors in exc.error_dict.items():
                    for e in errors:
                        index_error_map[index].append(
                            AttributeBulkCreateError(
                                path=to_camel_case(key),
                                message=e.messages[0],
                                code=e.code,
                            )
                        )
                instances_data_and_errors_list.append(
                    {"instance": None, "errors": index_error_map[index]}
                )
                continue

            if values_data:
                cls.create_values(instance, values_data, values, index, index_error_map)

        if error_policy == ErrorPolicyEnum.REJECT_FAILED_ROWS.value:
            for instance_data in instances_data_and_errors_list:
                if instance_data["errors"]:
                    instance_data["instance"] = None

        return instances_data_and_errors_list

    @classmethod
    def create_values(
        cls,
        attribute: models.Attribute,
        values_data: list[AttributeValueCreateInput],
        values: list[models.AttributeValue],
        attr_index: int,
        index_error_map: dict[int, list[AttributeBulkCreateError]],
    ):
        for value_index, value_data in enumerate(values_data):
            value = models.AttributeValue(attribute=attribute)

            try:
                value = cls.construct_instance(value, value_data)
                value.full_clean(exclude=["attribute", "slug"])
                values.append(value)
            except ValidationError as exc:
                for key, errors in exc.error_dict.items():
                    for e in errors:
                        path = f"values.{value_index}.{to_camel_case(key)}"
                        index_error_map[attr_index].append(
                            AttributeBulkCreateError(
                                path=path,
                                message=e.messages[0],
                                code=e.code,
                            )
                        )

    @classmethod
    def save(
        cls, instances_data_with_errors_list: list[dict]
    ) -> list[models.Attribute]:
        attributes_to_create: list = []
        values_to_create: list = []
        for attribute_data in instances_data_with_errors_list:
            attribute = attribute_data["instance"]

            if not attribute:
                continue

            attributes_to_create.append(attribute)

            if attribute_data["values"]:
                values_to_create.extend(attribute_data["values"])

        models.Attribute.objects.bulk_create(attributes_to_create)
        models.AttributeValue.objects.bulk_create(values_to_create)

        return attributes_to_create

    @classmethod
    def post_save_actions(cls, info: ResolveInfo, attributes: list[models.Attribute]):
        manager = get_plugin_manager_promise(info.context).get()
        for attribute in attributes:
            cls.call_event(manager.attribute_created, attribute)

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, root, info, **data):
        index_error_map: dict = defaultdict(list)
        error_policy = data.get("error_policy", ErrorPolicyEnum.REJECT_EVERYTHING.value)

        # clean and validate inputs
        cleaned_inputs_map = cls.clean_attributes(
            info, data["attributes"], index_error_map
        )
        instances_data_with_errors_list = cls.create_attributes(
            info, cleaned_inputs_map, error_policy, index_error_map
        )

        # check if errors occurred
        inputs_have_errors = next(
            (True for errors in index_error_map.values() if errors), False
        )

        if (
            inputs_have_errors
            and error_policy == ErrorPolicyEnum.REJECT_EVERYTHING.value
        ):
            results = get_results(instances_data_with_errors_list, True)
            return AttributeBulkCreate(count=0, results=results)

        # save all objects
        attributes = cls.save(instances_data_with_errors_list)

        # prepare and return data
        results = get_results(instances_data_with_errors_list)
        cls.post_save_actions(info, attributes)

        return AttributeBulkCreate(count=len(attributes), results=results)

from collections import defaultdict
from typing import Tuple, Type

import graphene
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db.models import F, Model, Q
from graphene.types.mutation import MutationOptions
from graphene.utils.str_converters import to_camel_case
from graphql import GraphQLError

from ....attribute import models as attribute_models
from ....core.tracing import traced_atomic_transaction
from ....discount import models as discount_models
from ....menu import models as menu_models
from ....page import models as page_models
from ....product import models as product_models
from ....shipping import models as shipping_models
from ...core import ResolveInfo
from ...core.descriptions import RICH_CONTENT
from ...core.doc_category import DOC_CATEGORY_MAP
from ...core.enums import ErrorPolicyEnum, TranslationErrorCode
from ...core.fields import JSONString
from ...core.mutations import BaseMutation, ModelMutation
from ...core.utils import from_global_id_or_error
from ...plugins.dataloaders import get_plugin_manager_promise
from .. import types as translation_types

TRANSLATABLE_CONTENT_TO_MODEL = {
    str(
        translation_types.ProductTranslatableContent
    ): product_models.Product._meta.object_name,
    str(
        translation_types.CollectionTranslatableContent
    ): product_models.Collection._meta.object_name,
    str(
        translation_types.CategoryTranslatableContent
    ): product_models.Category._meta.object_name,
    str(
        translation_types.AttributeTranslatableContent
    ): attribute_models.Attribute._meta.object_name,
    str(
        translation_types.AttributeValueTranslatableContent
    ): attribute_models.AttributeValue._meta.object_name,
    str(
        translation_types.ProductVariantTranslatableContent
    ): product_models.ProductVariant._meta.object_name,
    # Page Translation mutation reverses model and TranslatableContent
    page_models.Page._meta.object_name: str(translation_types.PageTranslatableContent),
    str(
        translation_types.ShippingMethodTranslatableContent
    ): shipping_models.ShippingMethod._meta.object_name,
    str(
        translation_types.SaleTranslatableContent
    ): discount_models.Sale._meta.object_name,
    str(
        translation_types.VoucherTranslatableContent
    ): discount_models.Voucher._meta.object_name,
    str(
        translation_types.MenuItemTranslatableContent
    ): menu_models.MenuItem._meta.object_name,
}


def validate_input_against_model(model: Type[Model], input_data: dict):
    data_to_validate = {key: value for key, value in input_data.items() if value}
    instance = model(**data_to_validate)
    all_fields = [field.name for field in model._meta.fields]
    exclude_fields = set(all_fields) - set(data_to_validate)
    instance.full_clean(exclude=exclude_fields, validate_unique=False)


class BaseTranslateMutation(ModelMutation):
    class Meta:
        abstract = True

    @classmethod
    def clean_node_id(cls, id: str) -> Tuple[str, Type[graphene.ObjectType]]:
        if not id:
            raise ValidationError(
                {"id": ValidationError("This field is required", code="required")}
            )

        try:
            node_type, node_pk = from_global_id_or_error(id)
        except GraphQLError:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Invalid ID has been provided.",
                        code=TranslationErrorCode.INVALID,
                    )
                }
            )

        # This mutation accepts either model IDs or translatable content IDs. Below we
        # check if provided ID refers to a translatable content which matches with the
        # expected model_type. If so, we transform the translatable content ID to model
        # ID.
        tc_model_type = TRANSLATABLE_CONTENT_TO_MODEL.get(node_type)

        if tc_model_type and tc_model_type == str(cls._meta.object_type):
            id = graphene.Node.to_global_id(tc_model_type, node_pk)

        return id, cls._meta.object_type

    @classmethod
    def validate_input(cls, input_data):
        validate_input_against_model(cls._meta.model, input_data)

    @classmethod
    def pre_update_or_create(cls, instance, input_data):
        return input_data

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, input, language_code
    ):
        node_id, model_type = cls.clean_node_id(id)
        instance = cls.get_node_or_error(info, node_id, only_type=model_type)
        cls.validate_input(input)

        input = cls.pre_update_or_create(instance, input)

        translation, created = instance.translations.update_or_create(
            language_code=language_code, defaults=input
        )
        manager = get_plugin_manager_promise(info.context).get()

        if created:
            cls.call_event(manager.translation_created, translation)
        else:
            cls.call_event(manager.translation_updated, translation)

        return cls(**{cls._meta.return_field_name: instance})


class NameTranslationInput(graphene.InputObjectType):
    name = graphene.String()


class SeoTranslationInput(graphene.InputObjectType):
    seo_title = graphene.String()
    seo_description = graphene.String()


class TranslationInput(NameTranslationInput, SeoTranslationInput):
    description = JSONString(description="Translated description." + RICH_CONTENT)


class BaseBulkTranslateMutation(BaseMutation):
    count = graphene.Int(
        required=True, description="Returns how many translations were created/updated."
    )

    class Arguments:
        error_policy = ErrorPolicyEnum(
            required=False,
            description="Policies of error handling. DEFAULT: "
            + ErrorPolicyEnum.REJECT_EVERYTHING.name,
        )

    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
        cls,
        base_model=None,
        translation_model=None,
        translation_fields=None,
        base_model_relation_field=None,
        result_type=None,
        _meta=None,
        **kwargs
    ):
        if not base_model:
            raise ImproperlyConfigured(
                "base model is required for bulk translation mutation"
            )
        if not translation_model:
            raise ImproperlyConfigured(
                "translation model is required for bulk translation mutation"
            )
        if not translation_fields:
            raise ImproperlyConfigured(
                "translation fields are required for bulk translation mutation"
            )
        if not result_type:
            raise ImproperlyConfigured(
                "result type is required for bulk translation mutation"
            )
        if not base_model_relation_field:
            raise ImproperlyConfigured(
                "base model relation field is required for bulk translation mutation"
            )
        if not _meta:
            _meta = MutationOptions(cls)

        _meta.base_model = base_model
        _meta.translation_model = translation_model
        _meta.translation_fields = translation_fields
        _meta.base_model_relation_field = base_model_relation_field
        _meta.result_type = result_type

        doc_category_key = f"{base_model._meta.app_label}.{base_model.__name__}"
        if "doc_category" not in kwargs and doc_category_key in DOC_CATEGORY_MAP:
            kwargs["doc_category"] = DOC_CATEGORY_MAP[doc_category_key]

        super().__init_subclass_with_meta__(_meta=_meta, **kwargs)

    @classmethod
    def clean_translations(cls, data_inputs, index_error_map):
        """Retrieve the instance channel id for channel permission accessible check."""
        raise NotImplementedError()

    @classmethod
    def pre_update_or_create(cls, translation, translation_fields):
        return translation_fields

    @classmethod
    def get_base_objects(cls, cleaned_inputs_map: dict):
        lookup = Q()
        for data in cleaned_inputs_map.values():
            if not data:
                continue

            if pk := data.get("id"):
                lookup |= Q(pk=pk)
            else:
                lookup |= Q(external_reference=data.get("external_reference"))

        attributes = cls._meta.base_model.objects.filter(lookup)
        return list(attributes)

    @classmethod
    def get_translations(cls, cleaned_inputs_map: dict, base_objects: list):
        lookup = Q(**{f"{cls._meta.base_model_relation_field}__in": base_objects})

        for data in cleaned_inputs_map.values():
            if not data:
                continue

            single_lookup = Q(language_code=data.get("language_code"))
            lookup |= single_lookup

        if hasattr(cls._meta.base_model, "external_reference"):
            translations = cls._meta.translation_model.objects.filter(lookup).annotate(
                base_object_external_reference=F(
                    f"{cls._meta.base_model_relation_field}__external_reference"
                ),
            )
        else:
            translations = cls._meta.translation_model.objects.filter(lookup)

        return list(translations)

    @classmethod
    def find_base_object(cls, pk, external_ref, base_objects, index_error_map, index):
        if pk:
            base_object = next((obj for obj in base_objects if str(obj.pk) == pk), None)
        else:
            base_object = next(
                (
                    obj
                    for obj in base_objects
                    if str(obj.external_reference) == external_ref
                ),
                None,
            )

        if not base_object:
            index_error_map[index].append(
                cls._meta.error_type_class(
                    message="Couldn't resolve to an object.",
                    code=TranslationErrorCode.NOT_FOUND.value,
                    path="id" if pk else "externalReference",
                )
            )

        return base_object

    @classmethod
    def find_translation(cls, pk, external_ref, language_code, translations):
        if pk:
            translation = next(
                (
                    t
                    for t in translations
                    if str(getattr(t, f"{cls._meta.base_model_relation_field}_id"))
                    == pk
                    and t.language_code == language_code
                ),
                None,
            )
        else:
            translation = next(
                (
                    t
                    for t in translations
                    if t.base_object_external_reference == external_ref
                    and t.language_code == language_code
                ),
                None,
            )

        return translation

    @classmethod
    def validate_translation_fields(cls, translation, translation_fields):
        translation_fields = cls.pre_update_or_create(translation, translation_fields)
        validate_input_against_model(cls._meta.translation_model, translation_fields)

    @classmethod
    def create_or_update_translation(cls, cleaned_inputs_map, index_error_map):
        instances_data_and_errors_list: list = []
        base_objects = cls.get_base_objects(cleaned_inputs_map)
        translations = cls.get_translations(cleaned_inputs_map, base_objects)

        for index, cleaned_input in cleaned_inputs_map.items():
            if not cleaned_input:
                instances_data_and_errors_list.append(
                    {"instance": None, "errors": index_error_map[index]}
                )
                continue

            obj_pk = cleaned_input.get("id")
            external_ref = cleaned_input.get("external_reference")
            language_code = cleaned_input["language_code"]
            translation_fields = cleaned_input["translation_fields"]

            base_object = cls.find_base_object(
                obj_pk, external_ref, base_objects, index_error_map, index
            )

            if not base_object:
                instances_data_and_errors_list.append(
                    {"instance": None, "errors": index_error_map[index]}
                )
                continue

            translation = cls.find_translation(
                obj_pk, external_ref, language_code, translations
            )

            try:
                if translation:
                    translation = cls.construct_instance(
                        translation, translation_fields
                    )
                    cls.validate_translation_fields(translation, translation_fields)
                    instances_data_and_errors_list.append(
                        {
                            "instance": translation,
                            "update": True,
                            "errors": index_error_map[index],
                        }
                    )
                else:
                    translation = cls._meta.translation_model(
                        language_code=language_code,
                        **{cls._meta.base_model_relation_field: base_object},
                        **translation_fields,
                    )
                    cls.validate_translation_fields(translation, translation_fields)
                    instances_data_and_errors_list.append(
                        {
                            "instance": translation,
                            "update": False,
                            "errors": index_error_map[index],
                        }
                    )
            except ValidationError as exc:
                for key, value in exc.error_dict.items():
                    for e in value:
                        index_error_map[index].append(
                            cls._meta.error_type_class(
                                path=to_camel_case(key),
                                message=e.messages[0],
                                code=e.code,
                            )
                        )
                instances_data_and_errors_list.append(
                    {"instance": None, "errors": index_error_map[index]}
                )
        return instances_data_and_errors_list

    @classmethod
    def save_translations(cls, instances_data_with_errors_list):
        translations_to_create: list = []
        translations_to_update: list = []

        for translation_data in instances_data_with_errors_list:
            translation = translation_data["instance"]

            if not translation:
                continue

            if translation_data["update"]:
                translations_to_update.append(translation)
            else:
                translations_to_create.append(translation)

        cls._meta.translation_model.objects.bulk_create(translations_to_create)
        cls._meta.translation_model.objects.bulk_update(
            translations_to_update, cls._meta.translation_fields
        )

        return translations_to_create, translations_to_update

    @classmethod
    def get_results(cls, instances_data_with_errors_list, reject_everything=False):
        if reject_everything:
            return [
                cls._meta.result_type(translation=None, errors=data.get("errors"))
                for data in instances_data_with_errors_list
            ]
        return [
            cls._meta.result_type(
                translation=data.get("instance"), errors=data.get("errors")
            )
            if data.get("instance")
            else cls._meta.result_type(translation=None, errors=data.get("errors"))
            for data in instances_data_with_errors_list
        ]

    @classmethod
    def post_save_actions(cls, info, created_translations, updated_translations):
        manager = get_plugin_manager_promise(info.context).get()

        for translation in created_translations:
            cls.call_event(manager.translation_created, translation)
        for translation in updated_translations:
            cls.call_event(manager.translation_updated, translation)

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, root, info, **data):
        index_error_map: dict = defaultdict(list)
        error_policy = data.get("error_policy", ErrorPolicyEnum.REJECT_EVERYTHING.value)

        # clean and validate inputs
        cleaned_inputs_map = cls.clean_translations(
            data["translations"], index_error_map
        )
        instances_data_with_errors_list = cls.create_or_update_translation(
            cleaned_inputs_map, index_error_map
        )

        if any([bool(error) for error in index_error_map.values()]):
            if error_policy == ErrorPolicyEnum.REJECT_EVERYTHING.value:
                results = cls.get_results(instances_data_with_errors_list, True)
                return cls(count=0, results=results)

            if error_policy == ErrorPolicyEnum.REJECT_FAILED_ROWS.value:
                for data in instances_data_with_errors_list:
                    if data["errors"] and data["instance"]:
                        data["instance"] = None

        new_translations, updated_translations = cls.save_translations(
            instances_data_with_errors_list
        )
        results = cls.get_results(instances_data_with_errors_list)

        cls.post_save_actions(info, new_translations, updated_translations)

        return cls(count=len(new_translations + updated_translations), results=results)

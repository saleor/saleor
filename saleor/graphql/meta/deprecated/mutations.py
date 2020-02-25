# Deprecated we should remove it in #5221
import graphene
from django.core.exceptions import ImproperlyConfigured
from graphene_django.registry import get_global_registry

from ...core.mutations import BaseMutation, get_model_name, get_output_fields
from .types import MetaInput, MetaPath

registry = get_global_registry()


class MetaUpdateOptions(graphene.types.mutation.MutationOptions):
    model = None
    return_field_name = None
    public = False


class BaseMetadataMutation(BaseMutation):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
        cls,
        arguments=None,
        model=None,
        public=False,
        return_field_name=None,
        _meta=None,
        **kwargs,
    ):
        if not model:
            raise ImproperlyConfigured("model is required for update meta mutation")
        if not _meta:
            _meta = MetaUpdateOptions(cls)
        if not arguments:
            arguments = {}
        if not return_field_name:
            return_field_name = get_model_name(model)
        fields = get_output_fields(model, return_field_name)

        _meta.model = model
        _meta.public = public
        _meta.return_field_name = return_field_name

        super().__init_subclass_with_meta__(_meta=_meta, **kwargs)
        cls._update_mutation_arguments_and_fields(arguments=arguments, fields=fields)

    @classmethod
    def get_store_method(cls, instance):
        return (
            getattr(instance, "store_value_in_metadata")
            if cls._meta.public
            else getattr(instance, "store_value_in_private_metadata")
        )

    @classmethod
    def get_meta_method(cls, instance):
        return (
            getattr(instance, "get_value_from_metadata")
            if cls._meta.public
            else getattr(instance, "get_value_from_private_metadata")
        )

    @classmethod
    def get_delete_method(cls, instance):
        return (
            getattr(instance, "delete_value_from_metadata")
            if cls._meta.public
            else getattr(instance, "delete_value_from_private_metadata")
        )

    @classmethod
    def get_instance(cls, info, **data):
        object_id = data.get("id")
        if object_id:
            model_type = registry.get_type_for_model(cls._meta.model)
            instance = cls.get_node_or_error(info, object_id, only_type=model_type)
        else:
            instance = cls._meta.model()
        return instance

    @classmethod
    def success_response(cls, instance):
        """Return a success response."""
        return cls(**{cls._meta.return_field_name: instance, "errors": []})


class UpdateMetaBaseMutation(BaseMetadataMutation):
    class Meta:
        abstract = True

    class Arguments:
        id = graphene.ID(description="ID of an object to update.", required=True)
        input = MetaInput(
            description="Fields required to update new or stored metadata item.",
            required=True,
        )

    @classmethod
    def perform_mutation(cls, root, info, **data):
        instance = cls.get_instance(info, **data)
        store_meta = cls.get_store_method(instance)

        metadata = data.pop("input")
        store_meta(items={metadata.key: metadata.value})
        instance.save()
        return cls.success_response(instance)


class ClearMetaBaseMutation(BaseMetadataMutation):
    class Meta:
        abstract = True

    class Arguments:
        id = graphene.ID(description="ID of a customer to update.", required=True)
        input = MetaPath(
            description="Fields required to identify stored metadata item.",
            required=True,
        )

    @classmethod
    def perform_mutation(cls, root, info, **data):
        instance = cls.get_instance(info, **data)
        delete_meta = cls.get_delete_method(instance)

        metadata = data.pop("input")

        delete_meta(metadata.key)
        instance.save()

        return cls.success_response(instance)

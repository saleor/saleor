import graphene
from django.core.exceptions import ValidationError
from graphql_jwt.exceptions import PermissionDenied

from ...core import models
from ...core.error_codes import MetadataErrorCode
from ..core.mutations import BaseMutation
from ..core.types.common import MetadataError
from .permissions import PRIVATE_META_PERMISSION_MAP, PUBLIC_META_PERMISSION_MAP
from .types import ObjectWithMetadata


class MetadataPermissionOptions(graphene.types.mutation.MutationOptions):
    permission_map = {}


class BaseMetadataMutation(BaseMutation):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
        cls, arguments=None, permission_map=[], _meta=None, **kwargs,
    ):
        if not _meta:
            _meta = MetadataPermissionOptions(cls)
        if not arguments:
            arguments = {}
        fields = {"item": graphene.Field(ObjectWithMetadata)}

        _meta.permission_map = permission_map

        super().__init_subclass_with_meta__(_meta=_meta, **kwargs)
        cls._update_mutation_arguments_and_fields(arguments=arguments, fields=fields)

    @classmethod
    def get_instance(cls, info, **data):
        object_id = data.get("id")
        if object_id:
            try:
                instance = cls.get_node_or_error(info, object_id)
            except ValidationError:
                instance = None
            if instance and issubclass(type(instance), models.ModelWithMetadata):
                return instance
        raise ValidationError(
            {
                "id": ValidationError(
                    f"Couldn't resolve to a item with meta: {object_id}",
                    code=MetadataErrorCode.NOT_FOUND.value,
                )
            }
        )

    @classmethod
    def get_permissions(cls, info, **data):
        object_id = data.get("id")
        if not object_id:
            return []
        type_name, object_pk = graphene.Node.from_global_id(object_id)
        permission = cls._meta.permission_map.get(type_name)
        if permission:
            return permission(info, object_pk)
        raise ValidationError(
            {
                "id": ValidationError(
                    f"Couldn't resolve permission to item: {object_id}",
                    code=MetadataErrorCode.INVALID.value,
                )
            }
        )

    @classmethod
    def mutate(cls, root, info, **data):
        try:
            permissions = cls.get_permissions(info, **data)
        except ValidationError as e:
            return cls.handle_errors(e)
        if not cls.check_permissions(info.context, permissions):
            raise PermissionDenied()
        return super().mutate(root, info, **data)

    @classmethod
    def success_response(cls, instance):
        """Return a success response."""
        return cls(**{"item": instance, "errors": []})


class MetadataInput(graphene.InputObjectType):
    key = graphene.String(required=True, description="Key of a metadata item.")
    value = graphene.String(required=True, description="Value of a metadata item.")


class UpdateMetadata(BaseMetadataMutation):
    class Meta:
        description = "Updates metadata of an object."
        permission_map = PUBLIC_META_PERMISSION_MAP
        error_type_class = MetadataError
        error_type_field = "metadata_errors"

    class Arguments:
        id = graphene.ID(description="ID of an object to update.", required=True)
        input = MetadataInput(
            description="Fields required to update the object's metadata.",
            required=True,
        )

    @classmethod
    def perform_mutation(cls, root, info, **data):
        instance = cls.get_instance(info, **data)
        if instance:
            metadata = data.pop("input")
            item = {metadata.key: metadata.value}
            instance.store_meta(items=item)
            instance.save(update_fields=["meta"])
        return cls.success_response(instance)


class DeleteMetadata(BaseMetadataMutation):
    class Meta:
        description = "Delete metadata of an object."
        permission_map = PUBLIC_META_PERMISSION_MAP
        error_type_class = MetadataError
        error_type_field = "metadata_errors"

    class Arguments:
        id = graphene.ID(description="ID of an object to update.", required=True)
        key = graphene.String(description="Metadata key to delete.", required=True)

    @classmethod
    def perform_mutation(cls, root, info, **data):
        instance = cls.get_instance(info, **data)
        if instance:
            metadata_key = data.pop("key")
            instance.delete_meta(metadata_key)
            instance.save(update_fields=["meta"])
        return cls.success_response(instance)


class UpdatePrivateMetadata(BaseMetadataMutation):
    class Meta:
        description = "Updates private metadata of an object."
        permission_map = PRIVATE_META_PERMISSION_MAP
        error_type_class = MetadataError
        error_type_field = "metadata_errors"

    class Arguments:
        id = graphene.ID(description="ID of an object to update.", required=True)
        input = MetadataInput(
            description=("Fields required to update the object's metadata."),
            required=True,
        )

    @classmethod
    def perform_mutation(cls, root, info, **data):
        instance = cls.get_instance(info, **data)
        if instance:
            metadata = data.pop("input")
            item = {metadata.key: metadata.value}
            instance.store_private_meta(items=item)
            instance.save(update_fields=["private_meta"])
        return cls.success_response(instance)


class DeletePrivateMetadata(BaseMetadataMutation):
    class Meta:
        description = "Delete object's private metadata."
        permission_map = PRIVATE_META_PERMISSION_MAP
        error_type_class = MetadataError
        error_type_field = "metadata_errors"

    class Arguments:
        id = graphene.ID(description="ID of an object to update.", required=True)
        key = graphene.String(description="Metadata key to delete.", required=True)

    @classmethod
    def perform_mutation(cls, root, info, **data):
        instance = cls.get_instance(info, **data)
        if instance:
            metadata_key = data.pop("key")
            instance.delete_private_meta(metadata_key)
            instance.save(update_fields=["private_meta"])
        return cls.success_response(instance)

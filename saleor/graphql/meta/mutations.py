import graphene
from django.core.exceptions import ValidationError
from graphql_jwt.exceptions import PermissionDenied

from ...account import models as account_models
from ...core import models
from ...core.error_codes import MetaErrorCode
from ...core.permissions import AccountPermissions, OrderPermissions, ProductPermissions
from ..core.mutations import BaseMutation
from ..core.types.common import MetaError
from .types import MetaInput, MetaPath, ObjectWithMetadata


def no_permissions(_info, _object_pk):
    return []


def public_user_permissions(info, user_pk):
    user = account_models.User.objects.filter(pk=user_pk).first()
    if not user:
        raise PermissionDenied()
    if info.context.user.pk == user.pk:
        return []
    if user.is_staff:
        return [AccountPermissions.MANAGE_STAFF]
    else:
        return [AccountPermissions.MANAGE_USERS]


def product_permissions(_info, _object_pk):
    return [ProductPermissions.MANAGE_PRODUCTS]


def order_permissions(_info, _object_pk):
    return [OrderPermissions.MANAGE_ORDERS]


def service_account_permissions(_info, _object_pk):
    return [AccountPermissions.MANAGE_SERVICE_ACCOUNTS]


PUBLIC_META_PERMISSION_MAP = {
    "Attribute": product_permissions,
    "Category": product_permissions,
    "Checkout": no_permissions,
    "Collection": product_permissions,
    "DigitalContent": product_permissions,
    "Fulfillment": order_permissions,
    "Order": no_permissions,
    "Product": product_permissions,
    "ProductType": product_permissions,
    "ProductVariant": product_permissions,
    "ServiceAccount": service_account_permissions,
    "User": public_user_permissions,
}


class MetaPermissionOptions(graphene.types.mutation.MutationOptions):
    permission_map = {}


class BaseMetadataMutation(BaseMutation):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
        cls, arguments=None, permission_map=[], _meta=None, **kwargs,
    ):
        if not _meta:
            _meta = MetaPermissionOptions(cls)
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
                    code=MetaErrorCode.NOT_FOUND.value,
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
                    code=MetaErrorCode.INVALID.value,
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


class UpdateMeta(BaseMetadataMutation):
    class Meta:
        description = "Updates metadata for item."
        permission_map = PUBLIC_META_PERMISSION_MAP
        error_type_class = MetaError
        error_type_field = "meta_errors"

    class Arguments:
        id = graphene.ID(description="ID of an object to update.", required=True)
        input = MetaInput(
            description="Fields required to update new or stored metadata item.",
            required=True,
        )

    @classmethod
    def perform_mutation(cls, root, info, **data):
        instance = cls.get_instance(info, **data)
        if instance:
            metadata = data.pop("input")
            stored_data = instance.get_meta(metadata.namespace, metadata.client_name)
            stored_data[metadata.key] = metadata.value
            instance.store_meta(
                namespace=metadata.namespace,
                client=metadata.client_name,
                item=stored_data,
            )
            instance.save()
        return cls.success_response(instance)


class ClearMeta(BaseMetadataMutation):
    class Meta:
        description = "Clear metadata for item."
        permission_map = PUBLIC_META_PERMISSION_MAP
        error_type_class = MetaError
        error_type_field = "meta_errors"

    class Arguments:
        id = graphene.ID(description="ID of an object to update.", required=True)
        input = MetaPath(
            description="Fields required to identify stored metadata item.",
            required=True,
        )

    @classmethod
    def perform_mutation(cls, root, info, **data):
        instance = cls.get_instance(info, **data)
        if instance:
            metadata = data.pop("input")
            # TODO: We should refactore clearing meta issue: XXXX
            # Don't forget about test test_clear_public_metadata_remove_empty_namespace
            stored_data = instance.get_meta(metadata.namespace, metadata.client_name)
            cleared_value = stored_data.pop(metadata.key, None)
            if not stored_data:
                instance.clear_stored_meta_for_client(
                    metadata.namespace, metadata.client_name
                )
                instance.save()
            elif cleared_value is not None:
                instance.store_meta(
                    namespace=metadata.namespace,
                    client=metadata.client_name,
                    item=stored_data,
                )
                instance.save()
        return cls.success_response(instance)

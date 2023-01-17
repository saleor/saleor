import logging
from typing import List, cast

import graphene
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import DatabaseError
from graphql.error.base import GraphQLError

from ...checkout import models as checkout_models
from ...checkout.models import Checkout
from ...core import models
from ...core.error_codes import MetadataErrorCode
from ...core.exceptions import PermissionDenied
from ...discount import models as discount_models
from ...menu import models as menu_models
from ...order import models as order_models
from ...product import models as product_models
from ...shipping import models as shipping_models
from ..channel import ChannelContext
from ..core import ResolveInfo
from ..core.mutations import BaseMutation
from ..core.types import MetadataError, NonNullList
from ..core.utils import from_global_id_or_error
from ..payment.utils import metadata_contains_empty_key
from .extra_methods import MODEL_EXTRA_METHODS, MODEL_EXTRA_PREFETCH
from .permissions import (
    PRIVATE_META_PERMISSION_MAP,
    PUBLIC_META_PERMISSION_MAP,
    AccountPermissions,
)
from .types import ObjectWithMetadata, get_valid_metadata_instance

logger = logging.getLogger(__name__)


def _save_instance(instance, metadata_field: str):
    fields = [metadata_field]

    try:
        if bool(instance._meta.get_field("updated_at")):
            fields.append("updated_at")
    except FieldDoesNotExist:
        pass

    try:
        instance.save(update_fields=fields)
    except DatabaseError as e:
        msg = (
            "Cannot update metadata for instance: %(instance)s. "
            "Updating not existing object. Details: %(details)s."
        )
        params = {
            "instance": str(instance),
            "details": str(e),
        }
        raise ValidationError(
            {
                "metadata": ValidationError(
                    msg, code=MetadataErrorCode.NOT_FOUND.value, params=params
                )
            }
        )


class MetadataPermissionOptions(graphene.types.mutation.MutationOptions):
    permission_map = {}


class BaseMetadataMutation(BaseMutation):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
        cls,
        arguments=None,
        permission_map=[],
        _meta=None,
        **kwargs,
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
    def get_instance(cls, info: ResolveInfo, /, *, id: str, qs=None, **kwargs):
        try:
            type_name, _ = from_global_id_or_error(id)
            # ShippingMethodType represents the ShippingMethod model
            if type_name == "ShippingMethodType":
                qs = shipping_models.ShippingMethod.objects

            return cls.get_node_or_error(info, id, qs=qs)
        except GraphQLError as e:
            if instance := cls.get_instance_by_token(id, qs):
                return instance
            raise ValidationError(
                {
                    "id": ValidationError(
                        str(e), code=MetadataErrorCode.GRAPHQL_ERROR.value
                    )
                }
            )

    @classmethod
    def get_instance_by_token(cls, object_id, qs):
        if not qs:
            if order := order_models.Order.objects.filter(id=object_id).first():
                return order
            if checkout := checkout_models.Checkout.objects.filter(
                token=object_id
            ).first():
                return checkout
            return None
        if qs and "token" in [field.name for field in qs.model._meta.get_fields()]:
            return qs.filter(token=object_id).first()

    @classmethod
    def validate_model_is_model_with_metadata(cls, model, object_id):
        if not issubclass(model, models.ModelWithMetadata) and not model == Checkout:
            raise ValidationError(
                {
                    "id": ValidationError(
                        f"Couldn't resolve to a item with meta: {object_id}",
                        code=MetadataErrorCode.NOT_FOUND.value,
                    )
                }
            )

    @classmethod
    def validate_metadata_keys(cls, metadata_list: List[dict]):
        if metadata_contains_empty_key(metadata_list):
            raise ValidationError(
                {
                    "input": ValidationError(
                        "Metadata key cannot be empty.",
                        code=MetadataErrorCode.REQUIRED.value,
                    )
                }
            )

    @classmethod
    def get_permissions(cls, info: ResolveInfo, type_name, object_pk, **data):
        if object_pk is None:
            return []
        object_id = data.get("id")
        model = cls.get_model_for_type_name(info, type_name)
        cls.validate_model_is_model_with_metadata(model, object_id)
        permission = cls._meta.permission_map.get(type_name)
        if permission:
            return permission(info, object_pk)
        raise NotImplementedError(
            f"Couldn't resolve permission to item: {object_id}. "
            "Make sure that type exists inside PRIVATE_META_PERMISSION_MAP "
            "and PUBLIC_META_PERMISSION_MAP"
        )

    @classmethod
    def get_model_for_type_name(cls, info: ResolveInfo, type_name):
        if type_name in ["ShippingMethodType", "ShippingMethod"]:
            return shipping_models.ShippingMethod

        graphene_type = info.schema.get_type(type_name).graphene_type

        if hasattr(graphene_type, "get_model"):
            return graphene_type.get_model()

        return graphene_type._meta.model

    @classmethod
    def check_permissions(cls, context, permissions=None):
        is_app = bool(getattr(context, "app", None))
        if is_app and permissions and AccountPermissions.MANAGE_STAFF in permissions:
            raise PermissionDenied(
                message="Apps are not allowed to perform this mutation."
            )
        return super().check_permissions(context, permissions)

    @classmethod
    def mutate(cls, root, info: ResolveInfo, **data):
        try:
            type_name, object_pk = cls.get_object_type_name_and_pk(data)
            permissions = cls.get_permissions(info, type_name, object_pk, **data)
        except GraphQLError as e:
            error = ValidationError(
                {"id": ValidationError(str(e), code="graphql_error")}
            )
            return cls.handle_errors(error)
        except ValidationError as e:
            return cls.handle_errors(e)

        if not cls.check_permissions(info.context, permissions):
            raise PermissionDenied(permissions=permissions)

        try:
            result = super().mutate(root, info, **data)
            if not result.errors:
                cls.perform_model_extra_actions(root, info, type_name, **data)
        except ValidationError as e:
            return cls.handle_errors(e)
        return result

    @classmethod
    def get_object_type_name_and_pk(cls, data):
        object_id = data.get("id")
        if not object_id:
            return None, None
        try:
            return from_global_id_or_error(object_id)
        except GraphQLError:
            if order := order_models.Order.objects.filter(id=object_id).first():
                return "Order", order.pk
            if checkout := checkout_models.Checkout.objects.filter(
                token=object_id
            ).first():
                return "Checkout", checkout.pk
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Couldn't resolve to a node.", code="graphql_error"
                    )
                }
            )

    @classmethod
    def perform_model_extra_actions(cls, root, info: ResolveInfo, type_name, **data):
        """Run extra metadata method based on mutating model."""
        if MODEL_EXTRA_METHODS.get(type_name):
            prefetch_method = MODEL_EXTRA_PREFETCH.get(type_name)
            if prefetch_method:
                data["qs"] = prefetch_method()
            instance = cls.get_instance(info, **data)
            MODEL_EXTRA_METHODS[type_name](instance, info, **data)

    @classmethod
    def success_response(cls, instance):
        """Return a success response."""
        # Wrap the instance with ChannelContext for models that use it.
        use_channel_context = any(
            [
                isinstance(instance, Model)
                for Model in [
                    discount_models.Sale,
                    discount_models.Voucher,
                    menu_models.Menu,
                    menu_models.MenuItem,
                    product_models.Collection,
                    product_models.Product,
                    product_models.ProductVariant,
                    shipping_models.ShippingMethod,
                    shipping_models.ShippingZone,
                ]
            ]
        )
        if use_channel_context:
            instance = ChannelContext(node=instance, channel_slug=None)
        return cls(**{"item": instance, "errors": []})


class MetadataInput(graphene.InputObjectType):
    key = graphene.String(required=True, description="Key of a metadata item.")
    value = graphene.String(required=True, description="Value of a metadata item.")


class UpdateMetadata(BaseMetadataMutation):
    class Meta:
        description = (
            "Updates metadata of an object. To use it, you need to have access to the "
            "modified object."
        )
        permission_map = PUBLIC_META_PERMISSION_MAP
        error_type_class = MetadataError
        error_type_field = "metadata_errors"

    class Arguments:
        id = graphene.ID(
            description="ID or token (for Order and Checkout) of an object to update.",
            required=True,
        )
        input = NonNullList(
            MetadataInput,
            description="Fields required to update the object's metadata.",
            required=True,
        )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str, input: List
    ):
        instance = cast(models.ModelWithMetadata, cls.get_instance(info, id=id))
        if instance:
            meta_instance = get_valid_metadata_instance(instance)
            cls.validate_metadata_keys(input)
            items = {data.key: data.value for data in input}
            meta_instance.store_value_in_metadata(items=items)
            _save_instance(meta_instance, "metadata")

        return cls.success_response(instance)


class DeleteMetadata(BaseMetadataMutation):
    class Meta:
        description = (
            "Delete metadata of an object. To use it, you need to have access to the "
            "modified object."
        )
        permission_map = PUBLIC_META_PERMISSION_MAP
        error_type_class = MetadataError
        error_type_field = "metadata_errors"

    class Arguments:
        id = graphene.ID(
            description="ID or token (for Order and Checkout) of an object to update.",
            required=True,
        )
        keys = NonNullList(
            graphene.String,
            description="Metadata keys to delete.",
            required=True,
        )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str, keys: List[str]
    ):
        instance = cast(models.ModelWithMetadata, cls.get_instance(info, id=id))
        if instance:
            meta_instance = get_valid_metadata_instance(instance)
            for key in keys:
                meta_instance.delete_value_from_metadata(key)
            _save_instance(meta_instance, "metadata")
        return cls.success_response(instance)


class UpdatePrivateMetadata(BaseMetadataMutation):
    class Meta:
        description = (
            "Updates private metadata of an object. To use it, you need to be an "
            "authenticated staff user or an app and have access to the modified object."
        )
        permission_map = PRIVATE_META_PERMISSION_MAP
        error_type_class = MetadataError
        error_type_field = "metadata_errors"

    class Arguments:
        id = graphene.ID(
            description="ID or token (for Order and Checkout) of an object to update.",
            required=True,
        )
        input = NonNullList(
            MetadataInput,
            description="Fields required to update the object's metadata.",
            required=True,
        )

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        instance = cls.get_instance(info, **data)
        if instance:
            meta_instance = get_valid_metadata_instance(instance)
            metadata_list = data.pop("input")
            cls.validate_metadata_keys(metadata_list)
            items = {data.key: data.value for data in metadata_list}
            meta_instance.store_value_in_private_metadata(items=items)
            _save_instance(meta_instance, "private_metadata")
        return cls.success_response(instance)


class DeletePrivateMetadata(BaseMetadataMutation):
    class Meta:
        description = (
            "Delete object's private metadata. To use it, you need to be an "
            "authenticated staff user or an app and have access to the modified object."
        )
        permission_map = PRIVATE_META_PERMISSION_MAP
        error_type_class = MetadataError
        error_type_field = "metadata_errors"

    class Arguments:
        id = graphene.ID(
            description="ID or token (for Order and Checkout) of an object to update.",
            required=True,
        )
        keys = NonNullList(
            graphene.String,
            description="Metadata keys to delete.",
            required=True,
        )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str, keys: List[str]
    ):

        instance = cls.get_instance(info, id=id)

        if instance:
            meta_instance = get_valid_metadata_instance(instance)
            for key in keys:
                meta_instance.delete_value_from_private_metadata(key)
            _save_instance(meta_instance, "private_metadata")
        return cls.success_response(instance)

import warnings
from typing import List

import graphene
from django.core.exceptions import ValidationError
from graphql.error.base import GraphQLError

from ...checkout import models as checkout_models
from ...core import models
from ...core.error_codes import MetadataErrorCode
from ...core.exceptions import PermissionDenied
from ...discount import models as discount_models
from ...menu import models as menu_models
from ...order import models as order_models
from ...product import models as product_models
from ...shipping import models as shipping_models
from ..channel import ChannelContext
from ..core.mutations import BaseMutation
from ..core.types.common import MetadataError
from ..core.utils import from_global_id_or_error
from ..payment.utils import metadata_contains_empty_key
from .extra_methods import MODEL_EXTRA_METHODS, MODEL_EXTRA_PREFETCH
from .permissions import PRIVATE_META_PERMISSION_MAP, PUBLIC_META_PERMISSION_MAP
from .types import ObjectWithMetadata


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
    def get_instance(cls, info, **data):
        object_id = data.get("id")
        qs = data.get("qs", None)

        try:
            type_name, _ = from_global_id_or_error(object_id)
            if type_name == "Order":
                warnings.warn("DEPRECATED. Use token for changing order metadata.")
            # ShippingMethod type isn't model-based class
            if type_name == "ShippingMethod":
                qs = shipping_models.ShippingMethod.objects
            return cls.get_node_or_error(info, object_id, qs=qs)
        except GraphQLError as e:
            if instance := cls.get_instance_by_token(object_id, qs):
                return instance
            raise ValidationError({"id": ValidationError(str(e), code="graphql_error")})

    @classmethod
    def get_instance_by_token(cls, object_id, qs):
        if not qs:
            if order := order_models.Order.objects.filter(token=object_id).first():
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
        if not issubclass(model, models.ModelWithMetadata):
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
    def get_permissions(cls, info, type_name, object_pk, **data):
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
    def get_model_for_type_name(cls, info, type_name):
        if type_name == "ShippingMethod":
            return shipping_models.ShippingMethod
        graphene_type = info.schema.get_type(type_name).graphene_type
        return graphene_type._meta.model

    @classmethod
    def mutate(cls, root, info, **data):
        type_name, object_pk = cls.get_object_type_name_and_pk(data)
        try:
            permissions = cls.get_permissions(info, type_name, object_pk, **data)
        except GraphQLError as e:
            error = ValidationError(
                {"id": ValidationError(str(e), code="graphql_error")}
            )
            return cls.handle_errors(error)
        except ValidationError as e:
            return cls.handle_errors(e)
        if not cls.check_permissions(info.context, permissions):
            raise PermissionDenied()
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
            if order := order_models.Order.objects.filter(token=object_id).first():
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
    def perform_model_extra_actions(cls, root, info, type_name, **data):
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
        description = "Updates metadata of an object."
        permission_map = PUBLIC_META_PERMISSION_MAP
        error_type_class = MetadataError
        error_type_field = "metadata_errors"

    class Arguments:
        id = graphene.ID(
            description="ID or token (for Order and Checkout) of an object to update.",
            required=True,
        )
        input = graphene.List(
            graphene.NonNull(MetadataInput),
            description="Fields required to update the object's metadata.",
            required=True,
        )

    @classmethod
    def perform_mutation(cls, root, info, **data):
        instance = cls.get_instance(info, **data)
        if instance:
            metadata_list = data.pop("input")
            cls.validate_metadata_keys(metadata_list)
            items = {data.key: data.value for data in metadata_list}
            instance.store_value_in_metadata(items=items)
            instance.save(update_fields=["metadata"])
        return cls.success_response(instance)


class DeleteMetadata(BaseMetadataMutation):
    class Meta:
        description = "Delete metadata of an object."
        permission_map = PUBLIC_META_PERMISSION_MAP
        error_type_class = MetadataError
        error_type_field = "metadata_errors"

    class Arguments:
        id = graphene.ID(
            description="ID or token (for Order and Checkout) of an object to update.",
            required=True,
        )
        keys = graphene.List(
            graphene.NonNull(graphene.String),
            description="Metadata keys to delete.",
            required=True,
        )

    @classmethod
    def perform_mutation(cls, root, info, **data):
        instance = cls.get_instance(info, **data)
        if instance:
            metadata_keys = data.pop("keys")
            for key in metadata_keys:
                instance.delete_value_from_metadata(key)
            instance.save(update_fields=["metadata"])
        return cls.success_response(instance)


class UpdatePrivateMetadata(BaseMetadataMutation):
    class Meta:
        description = "Updates private metadata of an object."
        permission_map = PRIVATE_META_PERMISSION_MAP
        error_type_class = MetadataError
        error_type_field = "metadata_errors"

    class Arguments:
        id = graphene.ID(
            description="ID or token (for Order and Checkout) of an object to update.",
            required=True,
        )
        input = graphene.List(
            graphene.NonNull(MetadataInput),
            description=("Fields required to update the object's metadata."),
            required=True,
        )

    @classmethod
    def perform_mutation(cls, root, info, **data):
        instance = cls.get_instance(info, **data)
        if instance:
            metadata_list = data.pop("input")
            cls.validate_metadata_keys(metadata_list)
            items = {data.key: data.value for data in metadata_list}
            instance.store_value_in_private_metadata(items=items)
            instance.save(update_fields=["private_metadata"])
        return cls.success_response(instance)


class DeletePrivateMetadata(BaseMetadataMutation):
    class Meta:
        description = "Delete object's private metadata."
        permission_map = PRIVATE_META_PERMISSION_MAP
        error_type_class = MetadataError
        error_type_field = "metadata_errors"

    class Arguments:
        id = graphene.ID(
            description="ID or token (for Order and Checkout) of an object to update.",
            required=True,
        )
        keys = graphene.List(
            graphene.NonNull(graphene.String),
            description="Metadata keys to delete.",
            required=True,
        )

    @classmethod
    def perform_mutation(cls, root, info, **data):
        instance = cls.get_instance(info, **data)
        if instance:
            metadata_keys = data.pop("keys")
            for key in metadata_keys:
                instance.delete_value_from_private_metadata(key)
            instance.save(update_fields=["private_metadata"])
        return cls.success_response(instance)

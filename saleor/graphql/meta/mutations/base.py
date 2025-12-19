import graphene
from django.core.exceptions import ValidationError
from graphql.error.base import GraphQLError

from ....attribute import models as attribute_models
from ....checkout import models as checkout_models
from ....core import models
from ....core.db.connection import allow_writer
from ....core.error_codes import MetadataErrorCode
from ....core.exceptions import PermissionDenied
from ....discount import models as discount_models
from ....discount.models import Promotion
from ....menu import models as menu_models
from ....order import models as order_models
from ....page import models as page_models
from ....product import models as product_models
from ....shipping import models as shipping_models
from ...core import ResolveInfo
from ...core.context import BaseContext, ChannelContext, SyncWebhookControlContext
from ...core.mutations import BaseMutation
from ...core.utils import from_global_id_or_error
from ..extra_methods import TYPE_EXTRA_METHODS
from ..permissions import AccountPermissions
from ..types import ObjectWithMetadata
from .utils import get_valid_metadata_instance


class MetadataPermissionOptions(graphene.types.mutation.MutationOptions):
    permission_map = {}


class BaseMetadataMutation(BaseMutation):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(  # type: ignore[override]
        cls,
        arguments=None,
        permission_map=None,
        _meta=None,
        **kwargs,
    ):
        if permission_map is None:
            permission_map = []
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
            type_name, db_id = from_global_id_or_error(id)
            # ShippingMethodType represents the ShippingMethod model
            if type_name == "ShippingMethodType":
                qs = shipping_models.ShippingMethod.objects
            # Sale is an old implementation of Promotion model
            if type_name == "Sale":
                return cls.get_old_sale_instance(id, db_id)

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
            ) from e

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
        return None

    @classmethod
    def get_old_sale_instance(cls, global_id, old_sale_id):
        if instance := discount_models.Promotion.objects.filter(
            old_sale_id=old_sale_id
        ).first():
            return instance
        raise ValidationError(
            {
                "id": ValidationError(
                    f"Couldn't resolve to a node: {global_id}", code="not_found"
                )
            }
        )

    @classmethod
    def validate_model_is_model_with_metadata(cls, model, object_id):
        if (
            not issubclass(model, models.ModelWithMetadata)
            and not model == checkout_models.Checkout
        ):
            raise ValidationError(
                {
                    "id": ValidationError(
                        f"Couldn't resolve to a item with meta: {object_id}",
                        code=MetadataErrorCode.NOT_FOUND.value,
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

        type_obj = info.schema.get_type(type_name)
        if not type_obj:
            raise GraphQLError(f"Invalid type: {type_name}")

        graphene_type = type_obj.graphene_type

        if hasattr(graphene_type, "get_model"):
            return graphene_type.get_model()

        return graphene_type._meta.model

    @classmethod
    def check_permissions(cls, context, permissions=None, **data):  # type: ignore[override]
        is_app = bool(getattr(context, "app", None))
        if is_app and permissions and AccountPermissions.MANAGE_STAFF in permissions:
            raise PermissionDenied(
                message="Apps are not allowed to perform this mutation."
            )
        return super().check_permissions(context, permissions)

    @classmethod
    @allow_writer()
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
            instance = cls.get_instance(info, id=data["id"])
        except ValidationError as e:
            return cls.handle_errors(e)

        if instance:
            metadata_instance = get_valid_metadata_instance(instance)
            old_metadata = dict(metadata_instance.metadata)
            old_private_metadata = dict(metadata_instance.private_metadata)
        else:
            old_metadata = {}
            old_private_metadata = {}

        try:
            result = super().mutate(root, info, **data)

            has_changed = False

            instance = result.item
            if isinstance(instance, BaseContext):
                instance = instance.node

            if instance:
                metadata_instance = get_valid_metadata_instance(instance)
                new_metadata = metadata_instance.metadata
                new_private_metadata = metadata_instance.private_metadata
                has_changed = (
                    old_metadata != new_metadata
                    or old_private_metadata != new_private_metadata
                )

            if not result.errors and has_changed:
                # Update fields for other models are performed in mutations together
                # with metadata update to perform one DB query.
                if isinstance(instance, checkout_models.Checkout):
                    instance.save(update_fields=["last_change"])
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
        except GraphQLError as e:
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
            ) from e

    @classmethod
    def perform_model_extra_actions(cls, root, info: ResolveInfo, type_name, **data):
        """Run extra metadata method based on mutating model."""
        if TYPE_EXTRA_METHODS.get(type_name):
            instance = cls.get_instance(info, **data)
            TYPE_EXTRA_METHODS[type_name](instance, info, **data)

    @classmethod
    def success_response(cls, instance):
        """Return a success response."""
        # Wrap the instance with ChannelContext for models that use it.
        use_channel_context = isinstance(
            instance,
            discount_models.Voucher
            | menu_models.Menu
            | menu_models.MenuItem
            | product_models.Collection
            | product_models.Product
            | product_models.ProductVariant
            | shipping_models.ShippingMethod
            | shipping_models.ShippingZone
            | attribute_models.Attribute
            | attribute_models.AttributeValue
            | page_models.Page,
        )

        use_channel_context = use_channel_context or (
            # For old sales migrated into promotions
            isinstance(instance, Promotion) and instance.old_sale_id
        )

        if use_channel_context:
            instance = ChannelContext(node=instance, channel_slug=None)

        use_webhook_sync_control_context = isinstance(
            instance,
            checkout_models.Checkout
            | checkout_models.CheckoutLine
            | order_models.Order
            | order_models.OrderLine
            | order_models.Fulfillment
            | order_models.FulfillmentLine,
        )

        if use_webhook_sync_control_context:
            instance = SyncWebhookControlContext(node=instance)

        return cls(item=instance, errors=[])

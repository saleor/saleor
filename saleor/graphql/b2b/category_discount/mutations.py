import graphene
from saleor.graphql.core import ResolveInfo
from .types import CategoryDiscount
from ...discount.enums import DiscountValueTypeEnum
from ...plugins.dataloaders import get_plugin_manager_promise
from ...core import ResolveInfo
from ...core.mutations import ModelMutation, ModelDeleteMutation
from ....b2b import models
from ....permission.enums import AccountPermissions, DiscountPermissions
from ...core.types import DiscountError
from ...core.scalars import PositiveDecimal
from ..customer_group.types import CustomerGroup


class CategoryDiscountInput(graphene.InputObjectType):
    category = graphene.ID()
    value = PositiveDecimal()
    value_type = DiscountValueTypeEnum()

class CategoryDiscountAddToGroupInput(CategoryDiscountInput):
    id = graphene.ID(required=True, description="id of the group for the discount to be added to")

class CreateDiscountAndAddToGroup(ModelMutation):
    class Arguments:
        input = CategoryDiscountAddToGroupInput(
            required=True
        )

    class Meta:
        description = "Create a category discount and add it to group"
        model = models.CategoryDiscount
        object_type = CategoryDiscount
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS, AccountPermissions.MANAGE_USERS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        customer_group = cls.get_node_or_error(
            info, cleaned_input['id'], field="customer_group_id", only_type=CustomerGroup
        )
        customer_group.category_discounts.add(instance)
        manager = get_plugin_manager_promise(info.context).get()

class UpdateCategoryDiscount(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = CategoryDiscountInput(required=True)

    class Meta:
        description = "Updates a category discount."
        model = models.CategoryDiscount
        object_type = CategoryDiscount
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

class DeleteCategoryDiscount(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=False)


    class Meta:
        description = "Deletes a category discount."
        model = models.CategoryDiscount
        object_type = CategoryDiscount
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

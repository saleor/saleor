from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError
from django.db.models import F, Q

from ....core.tracing import traced_atomic_transaction
from ....permission.enums import ProductPermissions
from ....warehouse import models
from ....warehouse.error_codes import StockBulkUpdateErrorCode
from ...core.descriptions import ADDED_IN_313, PREVIEW_FEATURE
from ...core.enums import ErrorPolicyEnum
from ...core.mutations import BaseMutation
from ...core.types import NonNullList, StockBulkUpdateError
from ...core.validators import validate_one_of_args_is_in_mutation
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Stock


class StockBulkResult(graphene.ObjectType):
    stock = graphene.Field(Stock, required=False, description="Stock data.")
    errors = NonNullList(
        StockBulkUpdateError,
        required=False,
        description="List of errors occurred on create or update attempt.",
    )


class StockBulkUpdateInput(graphene.InputObjectType):
    variant_id = graphene.ID(required=False, description="Variant ID.")
    variant_external_reference = graphene.String(
        required=False, description="Variant external reference."
    )
    warehouse_id = graphene.ID(required=False, description="Warehouse ID.")
    warehouse_external_reference = graphene.String(
        required=False, description="Warehouse external reference."
    )
    quantity = graphene.Int(
        required=True, description="Quantity of items available for sell."
    )


class StockBulkUpdate(BaseMutation):
    count = graphene.Int(
        required=True,
        default_value=0,
        description="Returns how many objects were updated.",
    )
    results = NonNullList(
        StockBulkResult,
        required=True,
        default_value=[],
        description="List of the updated stocks.",
    )

    class Arguments:
        stocks = NonNullList(
            StockBulkUpdateInput,
            required=True,
            description="Input list of stocks to update.",
        )
        error_policy = ErrorPolicyEnum(
            required=False,
            default_value=ErrorPolicyEnum.REJECT_EVERYTHING.value,
            description=(
                "Policies of error handling. DEFAULT: "
                + ErrorPolicyEnum.REJECT_EVERYTHING.name
            ),
        )

    class Meta:
        description = (
            "Updates stocks for a given variant and warehouse."
            + ADDED_IN_313
            + PREVIEW_FEATURE
        )
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = StockBulkUpdateError

    @classmethod
    def validate_variant(
        cls, variant_id, external_ref, stock_input, index, index_error_map
    ):
        errors_count = 0
        try:
            validate_one_of_args_is_in_mutation(
                "variant_id",
                variant_id,
                "variant_external_reference",
                external_ref,
                use_camel_case=True,
            )
        except ValidationError as exc:
            index_error_map[index].append(
                StockBulkUpdateError(
                    message=exc.message,
                    code=StockBulkUpdateErrorCode.INVALID.value,
                )
            )
            errors_count += 1

        if variant_id:
            try:
                type, variant_db_id = graphene.Node.from_global_id(variant_id)
                if type != "ProductVariant":
                    index_error_map[index].append(
                        StockBulkUpdateError(
                            field="variantId",
                            message="Invalid variantId.",
                            code=StockBulkUpdateErrorCode.INVALID.value,
                        )
                    )
                    errors_count += 1
                else:
                    stock_input["variant_id"] = variant_db_id
            except Exception:
                index_error_map[index].append(
                    StockBulkUpdateError(
                        field="variantId",
                        message="Invalid variantId.",
                        code=StockBulkUpdateErrorCode.INVALID.value,
                    )
                )
                errors_count += 1
        return errors_count

    @classmethod
    def validate_warehouse(
        cls,
        warehouse_id,
        external_ref,
        stock_input,
        index,
        index_error_map,
    ):
        errors_count = 0
        try:
            validate_one_of_args_is_in_mutation(
                "warehouse_id",
                warehouse_id,
                "warehouse_external_reference",
                external_ref,
                use_camel_case=True,
            )
        except ValidationError as exc:
            index_error_map[index].append(
                StockBulkUpdateError(
                    message=exc.message,
                    code=StockBulkUpdateErrorCode.INVALID.value,
                )
            )
            errors_count += 1

        if warehouse_id:
            try:
                type, warehouse_db_id = graphene.Node.from_global_id(warehouse_id)
                if type != "Warehouse":
                    index_error_map[index].append(
                        StockBulkUpdateError(
                            field="warehouseId",
                            message="Invalid warehouseId.",
                            code=StockBulkUpdateErrorCode.INVALID.value,
                        )
                    )
                    errors_count += 1
                else:
                    stock_input["warehouse_id"] = warehouse_db_id
            except Exception:
                index_error_map[index].append(
                    StockBulkUpdateError(
                        field="warehouseId",
                        message="Invalid warehouseId.",
                        code=StockBulkUpdateErrorCode.INVALID.value,
                    )
                )
                errors_count += 1
        return errors_count

    @classmethod
    def clean_stocks(cls, stocks_input, index_error_map):
        cleaned_inputs_map: dict = {}

        for index, stock_input in enumerate(stocks_input):
            base_error_count = 0
            variant_id = stock_input.get("variant_id")
            variant_external_ref = stock_input.get("variant_external_reference")
            warehouse_id = stock_input.get("warehouse_id")
            warehouse_external_ref = stock_input.get("warehouse_external_reference")

            base_error_count += cls.validate_variant(
                variant_id, variant_external_ref, stock_input, index, index_error_map
            )
            base_error_count += cls.validate_warehouse(
                warehouse_id,
                warehouse_external_ref,
                stock_input,
                index,
                index_error_map,
            )

            if stock_input.get("quantity") < 0:
                index_error_map[index].append(
                    StockBulkUpdateError(
                        field="quantity",
                        message="Quantity should not be less than 0.",
                        code=StockBulkUpdateErrorCode.INVALID.value,
                    )
                )
                base_error_count += 1

            if base_error_count > 0:
                cleaned_inputs_map[index] = None
            else:
                cleaned_inputs_map[index] = stock_input

        return cleaned_inputs_map

    @classmethod
    def _get_stock(
        cls, variant_id, variant_external_ref, warehouse_id, warehouse_external_ref
    ):
        if variant_id and warehouse_id:
            return (
                lambda stock: str(stock.warehouse_id) == warehouse_id
                and str(stock.product_variant_id) == variant_id
            )
        elif variant_external_ref and warehouse_id:
            return (
                lambda stock: str(stock.warehouse_id) == warehouse_id
                and stock.variant_external_reference == variant_external_ref
            )

        elif variant_external_ref and warehouse_external_ref:
            return (
                lambda stock: str(stock.warehouse_external_reference)
                == warehouse_external_ref
                and stock.variant_external_reference == variant_external_ref
            )
        else:
            return (
                lambda stock: stock.warehouse_external_reference
                == warehouse_external_ref
                and str(stock.product_variant_id) == variant_id
            )

    @classmethod
    def update_stocks(cls, cleaned_inputs_map, index_error_map):
        instances_data_and_errors_list: list = []
        stocks_list = cls.get_stocks(cleaned_inputs_map)

        for index, cleaned_input in cleaned_inputs_map.items():
            if not cleaned_input:
                instances_data_and_errors_list.append(
                    {"instance": None, "errors": index_error_map[index]}
                )
                continue

            variant_id = cleaned_input.get("variant_id")
            warehouse_id = cleaned_input.get("warehouse_id")
            variant_external_ref = cleaned_input.get("variant_external_reference")
            warehouse_external_ref = cleaned_input.get("warehouse_external_reference")

            filter_stock = list(
                filter(
                    cls._get_stock(
                        variant_id,
                        variant_external_ref,
                        warehouse_id,
                        warehouse_external_ref,
                    ),
                    stocks_list,
                )
            )
            if filter_stock:
                filter_stock[0].quantity = cleaned_input["quantity"]
                instances_data_and_errors_list.append(
                    {"instance": filter_stock[0], "errors": index_error_map[index]}
                )
            else:
                index_error_map[index].append(
                    StockBulkUpdateError(
                        message="Stock was not found.",
                        code=StockBulkUpdateErrorCode.NOT_FOUND.value,
                    )
                )
                instances_data_and_errors_list.append(
                    {"instance": None, "errors": index_error_map[index]}
                )

        return instances_data_and_errors_list

    @classmethod
    def get_stocks(cls, cleaned_inputs_map: dict) -> list[models.Stock]:
        lookup = Q()
        for stocks_input in cleaned_inputs_map.values():
            if not stocks_input:
                continue

            single_stock_lookup = Q()

            if variant_id := stocks_input.get("variant_id"):
                single_stock_lookup |= Q(product_variant_id=variant_id)
            else:
                single_stock_lookup |= Q(
                    product_variant__external_reference=stocks_input.get(
                        "variant_external_reference"
                    )
                )

            if warehouse_id := stocks_input.get("warehouse_id"):
                single_stock_lookup |= Q(warehouse_id=warehouse_id)
            else:
                single_stock_lookup |= Q(
                    warehouse__external_reference=stocks_input.get(
                        "variant_external_reference"
                    )
                )

            lookup |= single_stock_lookup

        stocks = models.Stock.objects.filter(lookup).annotate(
            variant_external_reference=F("product_variant__external_reference"),
            warehouse_external_reference=F("warehouse__external_reference"),
        )

        return list(stocks)

    @classmethod
    def save_stocks(cls, instances_data_with_errors_list):
        stocks_to_update = []

        for stock_data in instances_data_with_errors_list:
            stock = stock_data["instance"]
            if not stock:
                continue
            stocks_to_update.append(stock)

        models.Stock.objects.bulk_update(stocks_to_update, fields=["quantity"])

        return stocks_to_update

    @classmethod
    def post_save_actions(cls, info, instances):
        manager = get_plugin_manager_promise(info.context).get()
        for instance in instances:
            cls.call_event(manager.product_variant_stock_updated, instance)

    @classmethod
    def get_results(cls, instances_data_with_errors_list, reject_everything=False):
        if reject_everything:
            return [
                StockBulkResult(stock=None, errors=data.get("errors"))
                for data in instances_data_with_errors_list
            ]
        return [
            StockBulkResult(stock=data.get("instance"), errors=data.get("errors"))
            if data.get("instance")
            else StockBulkResult(stock=None, errors=data.get("errors"))
            for data in instances_data_with_errors_list
        ]

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        error_policy = data["error_policy"]
        index_error_map: dict = defaultdict(list)
        cleaned_inputs_map = cls.clean_stocks(data["stocks"], index_error_map)

        instances_data_with_errors_list = cls.update_stocks(
            cleaned_inputs_map, index_error_map
        )

        if any([True if error else False for error in index_error_map.values()]):
            if error_policy == ErrorPolicyEnum.REJECT_EVERYTHING.value:
                results = cls.get_results(instances_data_with_errors_list, True)
                return StockBulkUpdate(count=0, results=results)

            if error_policy == ErrorPolicyEnum.REJECT_FAILED_ROWS.value:
                for data in instances_data_with_errors_list:
                    if data["errors"] and data["instance"]:
                        data["instance"] = None

        updated_stocks = cls.save_stocks(instances_data_with_errors_list)

        # prepare and return data
        results = cls.get_results(instances_data_with_errors_list)

        cls.post_save_actions(info, updated_stocks)

        return StockBulkUpdate(count=len(updated_stocks), results=results)

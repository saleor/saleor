from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError
from django.db.models import F, Q

from ....core.tracing import traced_atomic_transaction
from ....permission.enums import ProductPermissions
from ....warehouse import models
from ....warehouse.error_codes import StockBulkUpdateErrorCode
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.utils import get_webhooks_for_event
from ...core.descriptions import ADDED_IN_313, PREVIEW_FEATURE
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.enums import ErrorPolicyEnum
from ...core.mutations import BaseMutation
from ...core.types import (
    BaseInputObjectType,
    BaseObjectType,
    NonNullList,
    StockBulkUpdateError,
)
from ...core.utils import WebhookEventInfo
from ...core.validators import validate_one_of_args_is_in_mutation
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Stock


class StockBulkResult(BaseObjectType):
    stock = graphene.Field(Stock, required=False, description="Stock data.")
    errors = NonNullList(
        StockBulkUpdateError,
        required=False,
        description="List of errors occurred on create or update attempt.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class StockBulkUpdateInput(BaseInputObjectType):
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

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


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
            description=(
                "Policies of error handling. DEFAULT: "
                + ErrorPolicyEnum.REJECT_EVERYTHING.name
            ),
        )

    class Meta:
        description = (
            "Updates stocks for a given variant and warehouse. Variant and warehouse "
            "selectors have to be the same for all stock inputs. Is not allowed to "
            "use 'variantId' in one input and 'variantExternalReference' in another."
            + ADDED_IN_313
            + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_PRODUCTS
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = StockBulkUpdateError
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.PRODUCT_VARIANT_STOCK_UPDATED,
                description="A product variant stock details were updated.",
            )
        ]

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
                    stock_input["product_variant_id"] = variant_db_id
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
    def get_selectors(cls, cleaned_inputs_map):
        return_error = False
        warehouse_selector = None
        variant_selector = None

        for stock_input in cleaned_inputs_map.values():
            if stock_input:
                warehouse_selector = (
                    "warehouse_id"
                    if cleaned_inputs_map[0].get("warehouse_id")
                    else "warehouse_external_reference"
                )
                variant_selector = (
                    "product_variant_id"
                    if cleaned_inputs_map[0].get("variant_id")
                    else "variant_external_reference"
                )
                break

        if not warehouse_selector or not variant_selector:
            return "warehouse_id", "product_variant_id"

        # check if all inputs have same selectors
        if not all(warehouse_selector in s for s in cleaned_inputs_map.values() if s):
            return_error = True

        if not all(variant_selector in s for s in cleaned_inputs_map.values() if s):
            return_error = True

        if return_error:
            message = (
                "All inputs should use the same selector for "
                "variant (`variantId` or `variantExternalReference`) and "
                "warehouse (`warehouseId` or `warehouseExternalReference`)."
            )
            raise ValidationError(
                message=message,
                code=StockBulkUpdateErrorCode.GRAPHQL_ERROR.value,
            )

        return warehouse_selector, variant_selector

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
        cls, warehouse_selector, variant_selector, warehouse_value, variant_value
    ):
        return (
            lambda stock: str(getattr(stock, warehouse_selector)) == warehouse_value
            and str(getattr(stock, variant_selector)) == variant_value
        )

    @classmethod
    def update_stocks(
        cls, cleaned_inputs_map, warehouse_selector, variant_selector, index_error_map
    ):
        instances_data_and_errors_list: list = []
        selectors_stock_map = cls.get_stocks(
            cleaned_inputs_map, warehouse_selector, variant_selector
        )

        for index, cleaned_input in cleaned_inputs_map.items():
            if not cleaned_input:
                instances_data_and_errors_list.append(
                    {"instance": None, "errors": index_error_map[index]}
                )
                continue

            warehouse_value = cleaned_input.get(warehouse_selector)
            variant_value = cleaned_input.get(variant_selector)

            filter_stock = selectors_stock_map.get(f"{variant_value}_{warehouse_value}")

            if filter_stock:
                filter_stock.quantity = cleaned_input["quantity"]
                instances_data_and_errors_list.append(
                    {"instance": filter_stock, "errors": index_error_map[index]}
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
    def get_stocks(
        cls, cleaned_inputs_map: dict, warehouse_selector: str, variant_selector: str
    ) -> dict[str, models.Stock]:
        warehouses = (
            stock_input[warehouse_selector]
            for stock_input in cleaned_inputs_map.values()
            if stock_input
        )

        variants = (
            stock_input[variant_selector]
            for stock_input in cleaned_inputs_map.values()
            if stock_input
        )

        if not warehouses or not variants:
            return {}

        if warehouse_selector == "warehouse_id":
            warehouse_lookup = Q(warehouse_id__in=warehouses)
        else:
            warehouse_lookup = Q(warehouse__external_reference__in=warehouses)

        if variant_selector == "product_variant_id":
            variant_lookup = Q(product_variant_id__in=variants)
        else:
            variant_lookup = Q(product_variant__external_reference__in=variants)

        stocks = models.Stock.objects.filter(
            warehouse_lookup & variant_lookup
        ).annotate(
            variant_external_reference=F("product_variant__external_reference"),
            warehouse_external_reference=F("warehouse__external_reference"),
        )

        selectors_stock_map = {
            f"{getattr(s, variant_selector)}_{getattr(s, warehouse_selector)}": s
            for s in stocks
        }
        return selectors_stock_map

    @classmethod
    def save_stocks(cls, instances_data_with_errors_list):
        stocks_to_update = [
            stock_data["instance"]
            for stock_data in instances_data_with_errors_list
            if stock_data["instance"]
        ]

        models.Stock.objects.bulk_update(stocks_to_update, fields=["quantity"])

        return stocks_to_update

    @classmethod
    def post_save_actions(cls, info, instances):
        manager = get_plugin_manager_promise(info.context).get()
        webhooks = get_webhooks_for_event(
            WebhookEventAsyncType.PRODUCT_VARIANT_STOCK_UPDATED
        )
        for instance in instances:
            cls.call_event(
                manager.product_variant_stock_updated, instance, webhooks=webhooks
            )

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
        error_policy = data.get("error_policy", ErrorPolicyEnum.REJECT_EVERYTHING.value)
        index_error_map: dict = defaultdict(list)
        cleaned_inputs_map = cls.clean_stocks(data["stocks"], index_error_map)

        warehouse_selector, variant_selector = cls.get_selectors(cleaned_inputs_map)

        instances_data_with_errors_list = cls.update_stocks(
            cleaned_inputs_map, warehouse_selector, variant_selector, index_error_map
        )

        if any([bool(error) for error in index_error_map.values()]):
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

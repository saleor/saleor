import typing
from collections import namedtuple

from django.db import transaction

from ..plugins.manager import PluginsManager
from ..warehouse.models import Allocation, Stock


class ProductVariantStockWebhookTrigger:
    _stock_data = namedtuple(
        "_stock_data", ("stock", "is_created", "prev_quantity", "current_quantity")
    )

    def __init__(self):
        self._stocks_data = []

    def append_stock_data(
        self, stock: Stock, is_created: bool, prev_quantity: int, current_quantity: int
    ) -> None:
        self._stocks_data.append(
            self._stock_data(stock, is_created, prev_quantity, current_quantity)
        )

    def append_stock_data_from_allocations(self, allocations: typing.List[Allocation]):
        for allocation in allocations:
            self.append_stock_data(
                allocation.stock,
                False,
                allocation.stock.quantity,
                allocation.stock.quantity - allocation.quantity_allocated,
            )

    def trigger_product_variant_back_in_stock_webhook(
        self, plugins_manager: PluginsManager
    ):
        for data in self._stocks_data:
            if self._is_variant_back_to_stock(data):
                transaction.on_commit(
                    lambda: plugins_manager.product_variant_back_in_stock(
                        data.stock.product_variant
                    )
                )

    def trigger_product_variant_out_of_stock_webhook(
        self, plugins_manager: PluginsManager
    ):
        for data in self._stocks_data:
            if data.current_quantity <= 0:
                transaction.on_commit(
                    lambda: plugins_manager.product_variant_out_of_stock(
                        data.stock.product_variant
                    )
                )

    def _is_variant_back_to_stock(
        self, updated_stock: "ProductVariantStockWebhookTrigger._stock_data"
    ):
        return (
            not updated_stock.is_created
            and updated_stock.prev_quantity <= 0
            and updated_stock.current_quantity > 0
        )

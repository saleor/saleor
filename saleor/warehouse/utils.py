from collections import namedtuple

from ..plugins.manager import get_plugins_manager


class ProductVariantStockWebhookTrigger:
    _stock_data = namedtuple(
        "_stock_data", ("stock", "is_created", "prev_quantity", "current_quantity")
    )

    def __init__(self):
        self._stocks_data = []
        self._plugins_manager = get_plugins_manager()

    def append_stock_data(self, stock, is_created, prev_quantity, current_quantity):
        self._stocks_data.append(
            self._stock_data(stock, is_created, prev_quantity, current_quantity)
        )

    def trigger_product_variant_back_in_stock_webhook(self):
        for data in self._stocks_data:
            if self._is_variant_back_to_stock(data):
                self._plugins_manager.product_variant_back_in_stock(
                    data.stock.product_variant
                )

    def trigger_product_variant_out_of_stock_webhook(self):
        for data in self._stocks_data:
            if data.current_quantity <= 0:
                self._plugins_manager.product_variant_out_of_stock(
                    data.stock.product_variant
                )

    def _is_variant_back_to_stock(self, updated_stock):
        return (
            not updated_stock.is_created
            and updated_stock.prev_quantity <= 0
            and updated_stock.current_quantity > 0
        )

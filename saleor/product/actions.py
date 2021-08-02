from django.db import transaction

from ..plugins.manager import PluginsManager
from ..warehouse.models import Stock


def check_and_trigger_back_in_stock_webhook(
    allocation, allocation_quantity_before, manager: PluginsManager
):
    available_stock_now = allocation.stock.available_quantity()

    if allocation_quantity_before == 0 and available_stock_now > 0:
        trigger_back_in_stock_webhook(allocation.stock, manager)


def trigger_out_of_stock_webhook(stock: "Stock", manager: PluginsManager):
    transaction.on_commit(lambda: manager.product_variant_out_of_stock(stock))


def trigger_back_in_stock_webhook(stock: "Stock", manager: PluginsManager):
    transaction.on_commit(lambda: manager.product_variant_back_in_stock(stock))

def get_available_quantity_for_stock(stock):
    """Count how many stock items are available."""
    return max(stock.quantity - stock.quantity_allocated, 0)

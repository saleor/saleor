class WarehouseClickAndCollectOption:
    DISABLED = "disabled"
    LOCAL_STOCK = "local"
    ALL_WAREHOUSES = "all"

    CHOICES = [
        (DISABLED, "Disabled"),
        (LOCAL_STOCK, "Local stock only"),
        (ALL_WAREHOUSES, "All warehouses"),
    ]

from ..permission.enums import DiscountPermissions, OrderPermissions, ProductPermissions

ALL_PRODUCTS_PERMISSIONS = [
    # List of permissions, where each of them allows viewing all products
    # (including unpublished).
    OrderPermissions.MANAGE_ORDERS,
    DiscountPermissions.MANAGE_DISCOUNTS,
    ProductPermissions.MANAGE_PRODUCTS,
]

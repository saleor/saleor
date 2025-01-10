import pytest

from ....app.models import AppExtension
from ....app.types import AppExtensionMount


@pytest.fixture
def app_with_extensions(app_with_token, permission_manage_products):
    first_app_extension = AppExtension(
        app=app_with_token,
        label="Create product with App",
        url="www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    extensions = AppExtension.objects.bulk_create(
        [
            first_app_extension,
            AppExtension(
                app=app_with_token,
                label="Update product with App",
                url="www.example.com/app-product-update",
                mount=AppExtensionMount.PRODUCT_DETAILS_MORE_ACTIONS,
            ),
        ]
    )
    first_app_extension.permissions.add(permission_manage_products)
    return app_with_token, extensions


@pytest.fixture
def removed_app_with_extensions(removed_app, permission_manage_products):
    first_app_extension = AppExtension(
        app=removed_app,
        label="Create product with App",
        url="www.example.com/app-product",
        mount=AppExtensionMount.PRODUCT_OVERVIEW_MORE_ACTIONS,
    )
    extensions = AppExtension.objects.bulk_create(
        [
            first_app_extension,
            AppExtension(
                app=removed_app,
                label="Update product with App",
                url="www.example.com/app-product-update",
                mount=AppExtensionMount.PRODUCT_DETAILS_MORE_ACTIONS,
            ),
        ]
    )
    first_app_extension.permissions.add(permission_manage_products)
    return removed_app, extensions

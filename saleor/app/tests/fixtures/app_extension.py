import pytest

from ....app.models import AppExtension


@pytest.fixture
def app_with_extensions(app_with_token, permission_manage_products):
    first_app_extension = AppExtension(
        app=app_with_token,
        label="Create product with App",
        url="www.example.com/app-product",
        mount="product_overview_more_actions",
    )
    extensions = AppExtension.objects.bulk_create(
        [
            first_app_extension,
            AppExtension(
                app=app_with_token,
                label="Update product with App",
                url="www.example.com/app-product-update",
                mount="product_details_more_actions",
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
        mount="product_overview_more_actions",
    )
    extensions = AppExtension.objects.bulk_create(
        [
            first_app_extension,
            AppExtension(
                app=removed_app,
                label="Update product with App",
                url="www.example.com/app-product-update",
                mount="product_details_more_actions",
            ),
        ]
    )
    first_app_extension.permissions.add(permission_manage_products)
    return removed_app, extensions

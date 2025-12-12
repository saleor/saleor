#!/usr/bin/env python
"""Script to create 50 mock apps with 4 extensions each.
Run with: python manage.py shell < create_mock_apps.py
or: python manage.py shell -c "exec(open('create_mock_apps.py').read())"
"""
import os

import django

# Setup Django environment if running standalone
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
    django.setup()

from saleor.app.models import App, AppExtension
from saleor.app.types import (
    DEFAULT_APP_TARGET,
    AppType,
    DeprecatedAppExtensionHttpMethod,
)


def create_mock_apps(num_apps=50, extensions_per_app=4):
    """Create mock apps with extensions."""

    print(f"Creating {num_apps} apps with {extensions_per_app} extensions each...")

    created_apps = []
    created_extensions = []

    for i in range(1, num_apps + 1):
        # Create app
        app = App.objects.create(
            name=f"Mock App {i}",
            type=AppType.THIRDPARTY,
            identifier=f"mock-app-{i}",
            about_app=f"This is a mock app number {i} for testing purposes.",
            data_privacy=f"Mock data privacy policy for app {i}.",
            data_privacy_url=f"https://example.com/app-{i}/privacy",
            homepage_url=f"https://example.com/app-{i}",
            support_url=f"https://example.com/app-{i}/support",
            configuration_url=f"https://example.com/app-{i}/configure",
            app_url=f"https://example.com/app-{i}/dashboard",
            manifest_url=f"https://example.com/app-{i}/manifest.json",
            version=f"1.{i % 10}.0",
            audience="https://example.com",
            is_active=True,
            is_installed=True,
            author=f"Mock Author {(i % 10) + 1}",
        )
        created_apps.append(app)

        # Create extensions for the app
        for j in range(1, extensions_per_app + 1):
            mount_options = [
                "PRODUCT_OVERVIEW_MORE_ACTIONS",
                "PRODUCT_DETAILS_MORE_ACTIONS",
                "ORDER_OVERVIEW_MORE_ACTIONS",
                "ORDER_DETAILS_MORE_ACTIONS",
                "CUSTOMER_OVERVIEW_MORE_ACTIONS",
                "CUSTOMER_DETAILS_MORE_ACTIONS",
                "NAVIGATION_CATALOG",
                "NAVIGATION_ORDERS",
            ]

            mount = mount_options[(j - 1) % len(mount_options)]

            extension = AppExtension.objects.create(
                app=app,
                label=f"Extension {j} for App {i}",
                url=f"https://example.com/app-{i}/extension-{j}",
                mount=mount,
                target=DEFAULT_APP_TARGET,
                http_target_method=DeprecatedAppExtensionHttpMethod.POST if j % 2 == 0 else DeprecatedAppExtensionHttpMethod.GET,
                settings={
                }
            )
            created_extensions.append(extension)

        if i % 10 == 0:
            print(f"Created {i} apps...")

    print("\nSuccessfully created:")
    print(f"  - {len(created_apps)} apps")
    print(f"  - {len(created_extensions)} extensions")
    print(f"\nTotal apps in database: {App.objects.count()}")
    print(f"Total extensions in database: {AppExtension.objects.count()}")


# Run the function when script is executed
create_mock_apps()

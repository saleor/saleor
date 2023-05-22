from typing import Union

manifest_fields_schema_extra: dict[str, Union[str, dict[str, str]]] = {
    "id": {
        "description": "Id of application used internally by Saleor",
    },
    "version": {"description": "App version"},
    "name": {
        "description": "App name displayed in the dashboard",
    },
    "about": {
        "description": "Description of the app displayed in the dashboard",
    },
    "token_target_url": {
        "description": "Endpoint used during process of app installation",
    },
    "required_saleor_version": {
        "description": "Version range, in the semver format, which specifies "
        "Saleor version required by the app. The field will be respected "
        "starting from Saleor 3.13"
    },
    "author": {
        "description": "App author name displayed in the dashboard "
        "(starting from Saleor 3.13)",
    },
    "permissions": {
        "description": "Array of permissions requested by the app",
    },
    "app_url": {
        "description": "App website rendered in the dashboard",
    },
    "configuration_url": {
        "description": "Address to the app configuration page, which is rendered "
        "in the dashboard (deprecated in Saleor 3.5, use appUrl instead)",
    },
    "data_privacy": {
        "description": "Short description of privacy policy displayed in "
        "the dashboard (deprecated in Saleor 3.5, use dataPrivacyUrl instead)",
    },
    "data_privacy_url": {
        "description": "URL to the full privacy policy",
    },
    "homepage_url": {
        "description": "External URL to the app homepage",
    },
    "support_url": {
        "description": "External URL to the page where " "app users can find support",
    },
    "webhooks": {"description": "List of webhooks that will be set"},
    "extensions": {
        "description": "List of extensions that will be mounted in Saleor's dashboard"
    },
}

manifest_schema_example = {
    "example": {
        "id": "example.app.wonderful",
        "version": "1.0.0",
        "requiredSaleorVersion": "^3.13",
        "name": "My Wonderful App",
        "author": "My Wonderful Company",
        "about": "My Wonderful App is a wonderful App for Saleor.",
        "permissions": ["MANAGE_USERS", "MANAGE_STAFF"],
        "appUrl": "http://localhost:3001/app",
        "configurationUrl": "htpp://localhost:3001/configuration",
        "tokenTargetUrl": "http://localhost:3001/register",
        "dataPrivacy": "Lorem ipsum",
        "dataPrivacyUrl": "http://localhost:3001/app-data-privacy",
        "homepageUrl": "http://localhost:3001/homepage",
        "supportUrl": "http://localhost:3001/support",
        "extensions": [
            {
                "label": "Create with Sample app",
                "mount": "PRODUCT_OVERVIEW_CREATE",
                "target": "POPUP",
                "permissions": ["MANAGE_PRODUCTS"],
                "url": "https://example.com/extension/",
            },
            {
                "label": "Create with App and redirect",
                "mount": "PRODUCT_OVERVIEW_CREATE",
                "target": "APP_PAGE",
                "permissions": ["MANAGE_PRODUCTS"],
                "url": "/extension/redirect",
            },
        ],
        "webhooks": [
            {
                "name": "Order created",
                "asyncEvents": ["ORDER_CREATED"],
                "query": "subscription { event { ... on OrderCreated { order { id }}}}",
                "targetUrl": "https://example.com/api/webhooks/order-created",
                "isActive": False,
            },
            {
                "name": "Multiple order's events",
                "asyncEvents": ["ORDER_CREATED", "ORDER_FULLY_PAID"],
                "query": "subscription { event { ... on OrderCreated { order "
                "{ id }} ... on OrderFullyPaid { order { id }}}}",
                "targetUrl": "https://example.com/api/webhooks/order-event",
                "isActive": True,
            },
        ],
    }
}

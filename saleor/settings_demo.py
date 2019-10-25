import os

from .settings import *  # noqa: F403

# DEMO-specific settings

PLUGINS += ["saleor.extensions.plugins.anonymize.plugin.AnonymizePlugin"]  # noqa: F405

MIDDLEWARE += ["saleor.core.middleware.ReadOnlyMiddleware"]  # noqa: F405

BRAINTREE_API_KEY = os.environ.get("BRAINTREE_API_KEY")
BRAINTREE_MERCHANT_ID = os.environ.get("BRAINTREE_MERCHANT_ID")
BRAINTREE_SECRET_API_KEY = os.environ.get("BRAINTREE_SECRET_API_KEY")

USE_JSON_CONTENT = True

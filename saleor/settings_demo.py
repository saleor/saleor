import logging
from urllib.parse import urlparse

from django.http.request import split_domain_port

from .settings import *  # noqa: F403

logger = logging.getLogger(__name__)

# DEMO-specific settings

PLUGINS += ["saleor.extensions.plugins.anonymize.plugin.AnonymizePlugin"]  # noqa: F405

MIDDLEWARE += ["saleor.core.middleware.ReadOnlyMiddleware"]  # noqa: F405

BRAINTREE_API_KEY = os.environ.get("BRAINTREE_API_KEY")
BRAINTREE_MERCHANT_ID = os.environ.get("BRAINTREE_MERCHANT_ID")
BRAINTREE_SECRET_API_KEY = os.environ.get("BRAINTREE_SECRET_API_KEY")

USE_JSON_CONTENT = True

SENTRY_ALLOWED_GRAPHQL_ORIGINS = ["pwa.getsaleor.com", "pwa.saleor.io"]


def before_send(event: dict, _hint: dict):
    ev_logger_name: str = event.get("logger", "")

    if ev_logger_name != "saleor.graphql.errors.handled":
        return event

    request: dict = event["request"]
    origin_url: str = request["headers"].get("Origin", "")

    try:
        parsed_url = urlparse(origin_url)
    except TypeError:
        pass
    else:
        domain, _ = split_domain_port(parsed_url.netloc)

        if domain in SENTRY_ALLOWED_GRAPHQL_ORIGINS:
            return event

    logger.info(f"Skipped error from ignored origin: {origin_url!r}")
    return None


sentry_sdk.init(
    os.environ["DEMO_SENTRY_DSN"],
    integrations=[DjangoIntegration()],
    before_send=before_send,
)

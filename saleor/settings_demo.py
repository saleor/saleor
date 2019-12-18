# flake8: noqa: F405
import logging
import re

from .settings import *  # noqa: F403

logger = logging.getLogger(__name__)

# DEMO-specific settings

PLUGINS += ["saleor.extensions.plugins.anonymize.plugin.AnonymizePlugin"]

MIDDLEWARE += ["saleor.core.middleware.ReadOnlyMiddleware"]

BRAINTREE_API_KEY = os.environ.get("BRAINTREE_API_KEY")
BRAINTREE_MERCHANT_ID = os.environ.get("BRAINTREE_MERCHANT_ID")
BRAINTREE_SECRET_API_KEY = os.environ.get("BRAINTREE_SECRET_API_KEY")

USE_JSON_CONTENT = True

PWA_ORIGIN = get_list(os.environ.get("PWA_ORIGIN", "pwa.saleor.io"))
PWA_DASHBOARD_URL_RE = re.compile("^https?://%s/dashboard/.*" % PWA_ORIGIN)

ROOT_EMAIL = os.environ.get("ROOT_EMAIL")


def _get_project_name_from_url(url: str) -> str:
    if PWA_DASHBOARD_URL_RE.match(url):
        return "dashboard"
    return "storefront"


def before_send(event: dict, _hint: dict):
    request: dict = event["request"]
    request_headers: dict = request["headers"]

    origin_url: str = request_headers.get("Origin", "")
    referer_url: str = request_headers.get("Referer", "")

    event["tags"] = {"project": _get_project_name_from_url(referer_url)}
    ev_logger_name: str = event.get("logger", "")

    if ev_logger_name != "saleor.graphql.errors.handled":
        return event

    # RFC6454, origin is the triple: uri-scheme, uri-host[, uri-port]
    if origin_url.endswith(PWA_ORIGIN):
        return event

    logger.info(f"Skipped error from ignored origin: {origin_url!r}")
    return None


sentry_sdk.init(
    os.environ["DEMO_SENTRY_DSN"],
    integrations=[DjangoIntegration()],
    before_send=before_send,
)

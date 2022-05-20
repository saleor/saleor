"""Settings file to run Saleor in "demo" mode.

Behavior specific to the demo mode:
- block API mutations that require admin permission (read-only mode for the dashboard
app)
- turn on anonymization plugin to anonymize data provided by customers in the public
checkout mutations
- configure Braintree payment gateway in sandbox mode if necessary environment
variables are set (see the `saleor.core.utils.random_data.configure_braintree` function
for more details)
- use DemoGraphQLView to render modified version of Playground that includes an example
GraphQL query
"""

# flake8: noqa: F405
import logging
import re

from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import ignore_logger

from ..settings import *  # noqa: F403, lgtm [py/polluting-import]

logger = logging.getLogger(__name__)

# Override urls to use different GraphQL view on demo
ROOT_URLCONF = "saleor.demo.urls"

PLUGINS += ["saleor.plugins.anonymize.plugin.AnonymizePlugin"]

GRAPHENE.setdefault("MIDDLEWARE", []).insert(  # type: ignore
    0, "saleor.graphql.middleware.ReadOnlyMiddleware"
)

BRAINTREE_API_KEY = os.environ.get("BRAINTREE_API_KEY")
BRAINTREE_MERCHANT_ID = os.environ.get("BRAINTREE_MERCHANT_ID")
BRAINTREE_SECRET_API_KEY = os.environ.get("BRAINTREE_SECRET_API_KEY")

if not (BRAINTREE_API_KEY and BRAINTREE_MERCHANT_ID and BRAINTREE_SECRET_API_KEY):
    logger.warning(
        "Some Braintree environment variables are missing. Set them to create the "
        "sandbox configuration in the demo mode with `populatedb` command."
    )

PWA_ORIGINS = get_list(os.environ.get("PWA_ORIGINS", "demo.saleor.io"))
PWA_DASHBOARD_URL_RE = re.compile("^https?://[^/]+/dashboard/.*")

ROOT_EMAIL = os.environ.get("ROOT_EMAIL")

# Remove "saleor.core" and add it after adding "saleor.demo", to have "populatedb"
# command overridden when using demo settings
# (see saleor.demo.management.commands.populatedb).
INSTALLED_APPS.remove("saleor.core")
INSTALLED_APPS += ["saleor.demo", "saleor.core"]
ENABLE_ACCOUNT_CONFIRMATION_BY_EMAIL = False


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
    if any(origin_url.endswith(pwa_origin) for pwa_origin in PWA_ORIGINS):
        return event

    logger.info(f"Skipped error from ignored origin: {origin_url!r}")
    return None


DEMO_SENTRY_DSN = os.environ.get("DEMO_SENTRY_DSN")
if DEMO_SENTRY_DSN:
    sentry_sdk.init(
        DEMO_SENTRY_DSN,
        integrations=[CeleryIntegration(), DjangoIntegration()],
        before_send=before_send,
    )
    ignore_logger("graphql.execution.utils")
    ignore_logger("graphql.execution.executor")
    ignore_logger("django.security.DisallowedHost")
